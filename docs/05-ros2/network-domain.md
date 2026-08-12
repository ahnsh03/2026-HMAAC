# ROS2 네트워크 · Domain

출처: PDF p.152–155

## Domain ID

- 같은 `ROS_DOMAIN_ID`를 가진 기기끼리만 DDS 통신
- 실습장에서 다른 팀과 섞이지 않도록 **팀 고유 ID**를 정하고 bashrc에 고정하는 것을 권장

```bash
export ROS_DOMAIN_ID=14   # 예시: 14팀 → 14 (팀 합의 후 확정)
echo 'export ROS_DOMAIN_ID=14' >> ~/.bashrc
```

## ROS_LOCALHOST_ONLY

외부 기기와 토픽이 섞이는 것을 막을 때:

```bash
export ROS_LOCALHOST_ONLY=1
echo "export ROS_LOCALHOST_ONLY=1" >> ~/.bashrc
```

`LOCALHOST_ONLY=1`이면 Domain이 같아도 **다른 머신과는 통신하지 않는다** (p.154).

실차 + 노트북 한 대만 쓸 때는 localhost only가 단순하다.  
노트북 여러 대로 분산할 계획이면 `0` + Domain ID 분리 전략을 팀에서 정한다.
