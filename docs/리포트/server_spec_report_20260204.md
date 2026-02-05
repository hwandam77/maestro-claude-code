# 서버 클러스터 시스템 스펙 보고서

**작성일:** 2026년 2월 4일
**대상 서버:** Cognit (10.5.5.11), Nexus (10.5.5.14)
**목적:** 클러스터 내 GPU 서버 하드웨어/소프트웨어 스펙 현황 기록

---

## 1. 스펙 요약 비교

| 항목 | Cognit (10.5.5.11) | Nexus (10.5.5.14) |
|------|---------------------|----------------------|
| **역할** | GPU 워커 노드 | vLLM 추론 서버 + 스토리지 허브 |
| **OS** | Ubuntu 22.04.5 LTS | Ubuntu 24.04.3 LTS |
| **CPU** | AMD Ryzen 7 5700X3D (8C/16T) | 2x Intel Xeon Platinum 8173M (56C/112T) |
| **RAM** | 64GB | 128GB |
| **GPU** | 2x RTX 3080 Ti (24GB 합계) | 2x RTX 3090 (48GB 합계) |
| **총 스토리지** | ~2TB | ~18TB |
| **NVIDIA Driver** | 580.105.08 | 590.48.01 |
| **CUDA** | 11.5 | nvcc 미설치 (드라이버 CUDA 13.1) |

---

## 2. Cognit (10.5.5.11) 상세 스펙

### 2.1 기본 정보

| 항목 | 사양 |
|------|------|
| **호스트명** | Cognit |
| **역할** | GPU 워커 노드 |
| **OS** | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| **Kernel** | 6.8.0-90-generic |

### 2.2 프로세서

| 항목 | 사양 |
|------|------|
| **CPU** | AMD Ryzen 7 5700X3D 8-Core Processor |
| **소켓** | 1 |
| **코어/소켓** | 8 |
| **스레드/코어** | 2 |
| **총 논리 CPU** | 16 |

### 2.3 메모리

| 항목 | 값 |
|------|-----|
| **총 용량** | 64GB |
| **사용 중** | 4.1GB |
| **가용** | 51GB |

### 2.4 GPU

| # | 모델 | VRAM | 드라이버 |
|---|------|------|---------|
| 0 | NVIDIA GeForce RTX 3080 Ti | 12GB | 580.105.08 |
| 1 | NVIDIA GeForce RTX 3080 Ti | 12GB | 580.105.08 |

- **CUDA Toolkit**: 11.5 (nvcc 설치됨)

### 2.5 스토리지

| 디바이스 | 용량 | 모델 | 유형 |
|----------|------|------|------|
| nvme0n1 | 1TB | WD_BLACK SN850X 1000GB | NVMe SSD |
| sda | 512GB | HS-SSD-HB1 512G | SATA SSD |
| sdb | 512GB | HS-SSD-HB1 512G | SATA SSD |

### 2.6 네트워크

| 인터페이스 | IP | 용도 |
|-----------|-----|------|
| wg0 | 10.5.5.11/32 | VPN (WireGuard) |
| bond0 | 192.168.1.2/24 | 내부 서버 간 통신 (active-backup) |
| ├ enp9s0 | (bond0 primary) | RTL8126 5GbE — Nexus enp166s0과 직결 |
| └ enp7s0 | (bond0 slave) | Intel 1GbE — Nexus eno1과 직결 (failover) |
| wlp5s0 | DHCP (172.16.x.x) | 인터넷 (WiFi, primary) |
| docker0 | 172.17.0.1/16 | Docker 기본 브릿지 |

- Docker 브릿지 네트워크 다수 구성 (br-a8f2da734545, br-f8c639d60e6d, br-024f34f222b6, br-2d853ba9eafb)
- bond0 관리: netplan (01-netcfg.yaml)

---

## 3. Nexus (10.5.5.14) 상세 스펙

### 3.1 기본 정보

| 항목 | 사양 |
|------|------|
| **호스트명** | vllm |
| **역할** | 메인 vLLM 추론 서버 + 스토리지 허브 |
| **OS** | Ubuntu 24.04.3 LTS (Noble Numbat) |
| **Kernel** | 6.8.0-94-generic |

### 3.2 프로세서

| 항목 | 사양 |
|------|------|
| **CPU** | 2x Intel Xeon Platinum 8173M @ 2.00GHz |
| **소켓** | 2 |
| **코어/소켓** | 28 |
| **스레드/코어** | 2 |
| **총 논리 CPU** | 112 |
| **NUMA 노드** | 2 (node0: 0-27,56-83 / node1: 28-55,84-111) |

### 3.3 메모리

| 항목 | 값 |
|------|-----|
| **총 용량** | 128GB |
| **사용 중** | 11GB |
| **가용** | 113GB |

### 3.4 GPU

| # | 모델 | VRAM | 드라이버 |
|---|------|------|---------|
| 0 | NVIDIA GeForce RTX 3090 | 24GB | 590.48.01 |
| 1 | NVIDIA GeForce RTX 3090 | 24GB | 590.48.01 |

- **CUDA Toolkit**: nvcc 미설치 (드라이버 레벨 CUDA 13.1 지원)

### 3.5 스토리지

| 디바이스 | 용량 | 모델 | 유형 |
|----------|------|------|------|
| nvme0n1 | 2TB | CT2000P3SSD8 (Crucial P3) | NVMe SSD |
| sde | 2TB | SSD 2TB | SATA SSD |
| sda | 4TB | WDC WD40EFRX-68N (WD Red) | HDD |
| sdb | 4TB | WDC WD40EFRX-68N (WD Red) | HDD |
| sdc | 4TB | WDC WD40EFRX-68N (WD Red) | HDD |
| sdd | 4TB | WDC WD40EFRX-68N (WD Red) | HDD |

- HDD 4x4TB: RAID/스토리지 풀 구성 (상세 구성은 별도 확인 필요)

### 3.6 네트워크

| 인터페이스 | IP | 용도 |
|-----------|-----|------|
| wg0 | 10.5.5.14/32 | VPN (WireGuard) |
| bond0 | 192.168.1.1/24 | 내부 서버 간 통신 (active-backup) |
| ├ enp166s0 | (bond0 primary) | RTL8127 10GbE — Cognit enp9s0과 직결 (5Gbps) |
| └ eno1 | (bond0 slave) | Intel 1GbE — Cognit enp7s0과 직결 (failover) |
| enp4s0f2np2 | 172.16.10.30/23 (고정) | 인터넷 (유선) + NAT GW |
| wlp34s0 | DHCP (172.16.10.x) | 인터넷 (Wi-Fi, 백업) |
| docker0 | 172.17.0.1/16 | Docker 기본 브릿지 |

- bond0 관리: nmcli (NetworkManager)

---

## 4. 클러스터 GPU 총합

| 노드 | GPU | 개별 VRAM | 합계 VRAM |
|------|-----|-----------|-----------|
| Nexus (10.5.5.14) | 2x RTX 3090 | 24GB | 48GB |
| Cognit (10.5.5.11) | 2x RTX 3080 Ti | 12GB | 24GB |
| **총합** | **4 GPUs** | - | **72GB** |

### 멀티노드 분산 추론 제약사항

- VRAM 불균형: RTX 3090 (24GB) vs RTX 3080 Ti (12GB)
- CUDA 버전 차이: 드라이버 590 (CUDA 13.1) vs 드라이버 580 (CUDA 11.5)
- 노드 간 통신: 192.168.1.x 내부 네트워크, 양쪽 bond0 (active-backup), 직결 케이블 5Gbps
- 직결 환경이므로 balance-alb 불가 (스위치 필요), active-backup만 사용

---

## 5. 참고사항

### SSH 설정 이슈

- `~/.ssh/config` 150번 줄에 `id_ed25519_vllm` 키를 참조하는 설정이 있으나 해당 키 파일 미존재
- `id_rsa` 키로 정상 접속 가능하므로 운영에는 영향 없음
- config 정리 권장

### 소프트웨어 버전 차이

| 항목 | Cognit | Nexus |
|------|---------|----------|
| Ubuntu | 22.04 | 24.04 |
| Kernel | 6.8.0-90 | 6.8.0-94 |
| NVIDIA Driver | 580.105.08 | 590.48.01 |
| CUDA (nvcc) | 11.5 | 미설치 |

---

**작성:** AI Assistant
**최종 수정:** 2026-02-04
