#!/usr/bin/env python3
"""Replay /detections through the extractor IPM and sweep cutting × p × β."""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

_WS = Path(__file__).resolve().parents[1]
_PKG = _WS / 'src' / 'camera_perception_pkg' / 'camera_perception_pkg'
sys.path.insert(0, str(_PKG))
from lib import camera_perception_func_lib as CPFL  # noqa: E402

SRC_MAT = [[238, 316], [402, 313], [501, 476], [155, 476]]
CUTS = (0, 40, 80, 120, 160)
POWERS = (0.0, 1.0, 2.0)
BLENDS = (0.0, 0.25, 0.5, 0.75, 1.0)
REF_X = 320.0
JUMP_P95_MAX = 20.0
MIN_AREA = 1000.0


def _dst_mat(h, w):
    return [
        [round(w * 0.3), round(h * 0.0)],
        [round(w * 0.7), round(h * 0.0)],
        [round(w * 0.7), h],
        [round(w * 0.3), h],
    ]


def _iter_detections(uri):
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    from rosbag2_py import ConverterOptions, SequentialReader, StorageOptions

    reader = SequentialReader()
    reader.open(
        StorageOptions(uri=uri, storage_id='sqlite3'),
        ConverterOptions(input_serialization_format='cdr', output_serialization_format='cdr'),
    )
    types = {t.name: get_message(t.type) for t in reader.get_all_topics_and_types()}
    while reader.has_next():
        topic, data, _stamp = reader.read_next()
        if topic != '/detections':
            continue
        yield deserialize_message(data, types[topic])


def _bev_from_detection(msg):
    if not msg.detections:
        return None
    filled = CPFL.draw_filled_masks(msg, cls_name='lane2', color=255)
    if filled.size == 0 or not np.any(filled):
        return None
    h, w = filled.shape[:2]
    return CPFL.bird_convert(filled, srcmat=SRC_MAT, dstmat=_dst_mat(h, w))


def _stats(values):
    arr = np.asarray(values, dtype=np.float64)
    finite = arr[np.isfinite(arr)]
    n = len(arr)
    nan_frac = 1.0 - (len(finite) / n) if n else 1.0
    if finite.size == 0:
        return {
            'n': n,
            'nan': nan_frac,
            'mean': math.nan,
            'median': math.nan,
            'bias': math.nan,
            'abs_p95': math.nan,
            'jump_med': math.nan,
            'jump_p95': math.nan,
        }
    jumps = np.abs(np.diff(finite))
    return {
        'n': n,
        'nan': nan_frac,
        'mean': float(np.mean(finite)),
        'median': float(np.median(finite)),
        'bias': float(np.mean(finite) - REF_X),
        'abs_p95': float(np.percentile(np.abs(finite - REF_X), 95)),
        'jump_med': float(np.median(jumps)) if jumps.size else 0.0,
        'jump_p95': float(np.percentile(jumps, 95)) if jumps.size else 0.0,
    }


def sweep_bag(uri):
    bevs = []
    for msg in _iter_detections(uri):
        bev = _bev_from_detection(msg)
        if bev is not None:
            bevs.append(bev)
    series = {
        (cut, power, blend): []
        for cut in CUTS
        for power in POWERS
        for blend in BLENDS
    }
    for bev in bevs:
        for cut in CUTS:
            roi = CPFL.roi_rectangle_below(bev, cutting_idx=cut)
            far_x, _area = CPFL.largest_component_center(roi, min_area=MIN_AREA)
            near_by_p = {}
            for power in POWERS:
                near_x, _ = CPFL.row_midpoint_center(
                    roi, power=power, min_area=MIN_AREA
                )
                near_by_p[power] = near_x
            for power in POWERS:
                for blend in BLENDS:
                    cx = CPFL.blend_lane_center(far_x, near_by_p[power], blend)
                    series[(cut, power, blend)].append(
                        float(cx) if cx is not None else math.nan
                    )
    return {key: _stats(vals) for key, vals in series.items()}, len(bevs)


def _fmt(stat):
    return (
        f"mean={stat['mean']:6.1f} med={stat['median']:6.1f} "
        f"bias={stat['bias']:+6.1f} |e|p95={stat['abs_p95']:5.1f} "
        f"j_p95={stat['jump_p95']:5.1f} nan={stat['nan']*100:4.1f}%"
    )


def pick_winner(bag_stats):
    """Smallest |mean-320| among jump_p95 <= 20, same combo on both bags if possible."""
    keys = list(next(iter(bag_stats.values())).keys())
    scores = []
    for key in keys:
        ok = True
        abs_bias = []
        for stats in bag_stats.values():
            st = stats[key]
            if not math.isfinite(st['bias']) or st['jump_p95'] > JUMP_P95_MAX:
                ok = False
                break
            abs_bias.append(abs(st['bias']))
        if not ok:
            continue
        scores.append((float(np.mean(abs_bias)), key))
    scores.sort()
    return scores[0][1] if scores else None, scores[:8]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--bags',
        nargs='+',
        default=[
            str(_WS / 'bags' / 'main_20260814_102829' / 'eval'),
            str(_WS / 'bags' / 'main_20260814_103107' / 'eval'),
        ],
    )
    args = parser.parse_args()

    bag_stats = {}
    for uri in args.bags:
        name = Path(uri).parent.name
        print(f'\n===== {name} =====', flush=True)
        stats, n_bev = sweep_bag(uri)
        bag_stats[name] = stats
        print(f'frames_with_lane2={n_bev}')
        print(f'{"cut":>4} {"p":>3} {"b":>4}  metrics')
        for cut in CUTS:
            for power in POWERS:
                for blend in BLENDS:
                    key = (cut, power, blend)
                    print(f'{cut:4d} {power:3.0f} {blend:4.2f}  {_fmt(stats[key])}')

    winner, top = pick_winner(bag_stats)
    print('\n===== pick (|bias| mean, jump_p95<=20) =====')
    if winner is None:
        print('no combo passed jump_p95<=20')
        return 1
    cut, power, blend = winner
    print(f'winner cut={cut} p={power:g} beta={blend:g}')
    for name, stats in bag_stats.items():
        print(f'  {name}: {_fmt(stats[winner])}')
        print(f'  {name} suggested vehicle_center_x={stats[winner]["median"]:.1f}')
    print('top:')
    for score, key in top:
        print(f'  |bias|={score:5.1f}  cut={key[0]} p={key[1]:g} beta={key[2]:g}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
