# 0006: KCBERT 입력 truncation

- 날짜: 2026-11-07
- 상태: 대기 <!-- 진행중 | 완료 | 보류 -->
- 담당 에이전트: backend
- 우선순위: 상

## 목표
- **FR-API-06** 긴 입력 처리: 병합된 턴이 KCBERT 최대 입력 길이(300 토큰)를 넘어도 분석이 실패하지 않는다.

## 범위
- 포함:
- 제외:

## 완료 조건
- [ ] `python ai/harness.py check` error 0
- [ ] FR-API-06: 300 토큰을 넘는 턴도 등급이 산출된다(truncation 적용).

## 계획
tokenizer(text, truncation=True, max_length=300). 학습 노트북 03의 max_length와 일치하는지 확인

## 결과
<!-- 변경 파일, 검증 결과(실행한 것 / 실행 못 한 것), 리뷰 지적과 처리 -->
