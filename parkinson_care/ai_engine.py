"""
파킨슨병 환자 관리 앱 - AI 분석 엔진
OpenRouter API (Gemini) + librosa 음성 분석
"""
import json
import threading
import requests
import numpy as np
import os

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, AI_MODEL, MEDIA_DIR


class AIEngine:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = AI_MODEL

    def _call_api(self, messages, max_tokens=1500):
        """OpenRouter API 호출"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Parkinson Care App",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[AI 연결 오류] {str(e)}\n오프라인 모드로 분석합니다."

    # ── 증상 분석 ──
    def analyze_symptoms(self, symptoms_text, callback=None):
        """증상 텍스트를 AI에게 분석 요청"""
        def _run():
            messages = [
                {
                    "role": "system",
                    "content": (
                        "당신은 파킨슨병 전문 의료 보조 AI입니다. 한국어로 답변하세요. "
                        "환자가 보고하는 증상을 분석하고, 가능한 원인과 권장 재활 치료를 제안하세요. "
                        "반드시 '이 분석은 참고용이며, 전문 의료진의 상담이 필요합니다'라는 면책 조항을 포함하세요. "
                        "답변 형식: \n1. 증상 분석\n2. 가능한 원인\n3. 권장 재활 치료\n4. 주의사항"
                    ),
                },
                {
                    "role": "user",
                    "content": f"다음 파킨슨병 환자의 증상을 분석해주세요:\n\n{symptoms_text}",
                },
            ]
            result = self._call_api(messages)
            if callback:
                callback(result)
            return result

        if callback:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return None
        else:
            return _run()

    # ── 재활 치료 추천 ──
    def recommend_rehab(self, symptom_data, current_rehabs=None, callback=None):
        """증상 기반 재활 치료 추천"""
        def _run():
            rehab_info = ""
            if current_rehabs:
                rehab_info = f"\n현재 수행 중인 재활 치료: {', '.join(current_rehabs)}"

            messages = [
                {
                    "role": "system",
                    "content": (
                        "당신은 파킨슨병 재활 치료 전문 AI입니다. 한국어로 답변하세요. "
                        "환자의 증상에 맞는 재활 치료를 추천하세요. "
                        "추천할 수 있는 치료 종류: 제자리 걷기, 한 발로 균형 잡기, 계단 오르내리기, "
                        "의자에서 일어서기, 팔 들어올리기, 스트레칭, 손가락 운동, 표정 근육 운동, "
                        "발성 훈련, 글씨 쓰기, 실내 자전거, 호흡 운동, 수치료, 태극권. "
                        "각 치료의 횟수와 주의사항도 포함하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": f"다음 증상에 맞는 재활 치료를 추천해주세요:\n{symptom_data}{rehab_info}",
                },
            ]
            result = self._call_api(messages)
            if callback:
                callback(result)
            return result

        if callback:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return None
        else:
            return _run()

    # ── 재활 효과 분석 ──
    def analyze_rehab_progress(self, rehab_stats, symptom_stats, callback=None):
        """재활 치료 진행 상황 분석"""
        def _run():
            messages = [
                {
                    "role": "system",
                    "content": (
                        "당신은 파킨슨병 재활 치료 효과 분석 AI입니다. 한국어로 답변하세요. "
                        "환자의 재활 치료 기록과 증상 변화를 분석하여 효과를 평가하고 개선 방향을 제안하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"재활 치료 현황:\n{rehab_stats}\n\n"
                        f"증상 현황:\n{symptom_stats}\n\n"
                        "위 데이터를 바탕으로 재활 치료 효과를 분석해주세요."
                    ),
                },
            ]
            result = self._call_api(messages)
            if callback:
                callback(result)
            return result

        if callback:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return None
        else:
            return _run()

    # ── 음성 분석 ──
    def analyze_voice(self, audio_path, callback=None):
        """음성 파일 분석 (librosa 기반)"""
        def _run():
            try:
                import librosa
                import soundfile as sf

                # 오디오 로드
                y, sr = librosa.load(audio_path, sr=22050)

                # 특징 추출
                features = self._extract_voice_features(y, sr)

                # AI 해석 요청
                interpretation = self._interpret_voice(features)

                result = {
                    "features": features,
                    "interpretation": interpretation,
                    "status": "success",
                }
            except Exception as e:
                result = {
                    "features": None,
                    "interpretation": f"음성 분석 오류: {str(e)}",
                    "status": "error",
                }

            if callback:
                callback(result)
            return result

        if callback:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return None
        else:
            return _run()

    def _extract_voice_features(self, y, sr):
        """librosa로 음성 특징 추출"""
        import librosa

        # F0 (기본 주파수)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
        )
        f0_valid = f0[~np.isnan(f0)] if f0 is not None else np.array([0])

        # Jitter (주파수 변동) - 연속 피치 간 차이
        if len(f0_valid) > 1:
            jitter = np.mean(np.abs(np.diff(f0_valid))) / np.mean(f0_valid) * 100
        else:
            jitter = 0.0

        # Shimmer (진폭 변동)
        rms = librosa.feature.rms(y=y)[0]
        if len(rms) > 1:
            shimmer = np.mean(np.abs(np.diff(rms))) / np.mean(rms) * 100
        else:
            shimmer = 0.0

        # HNR (조음대잡음비)
        S = np.abs(librosa.stft(y))
        harmonic, percussive = librosa.decompose.hpss(S)
        h_energy = np.sum(harmonic ** 2)
        p_energy = np.sum(percussive ** 2)
        hnr = 10 * np.log10(h_energy / (p_energy + 1e-10)) if p_energy > 0 else 0

        # MFCC
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = mfccs.mean(axis=1).tolist()

        # 리스크 레벨 판단
        risk = "낮음"
        if jitter > 1.5 or shimmer > 5.0 or hnr < 15:
            risk = "높음"
        elif jitter > 0.8 or shimmer > 3.0 or hnr < 20:
            risk = "보통"

        return {
            "f0_mean": float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0,
            "f0_std": float(np.std(f0_valid)) if len(f0_valid) > 0 else 0,
            "jitter": round(float(jitter), 4),
            "shimmer": round(float(shimmer), 4),
            "hnr": round(float(hnr), 2),
            "mfcc_means": [round(x, 4) for x in mfcc_means],
            "duration": round(float(len(y) / sr), 2),
            "risk_level": risk,
        }

    def _interpret_voice(self, features, callback=None):
        """AI로 음성 분석 결과 해석"""
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 파킨슨병 음성 분석 전문 AI입니다. 한국어로 답변하세요. "
                    "음성 분석 수치를 해석하고, 파킨슨병 관련 음성 이상 여부를 판단해주세요. "
                    "정상 범위 참고: Jitter < 1.0%, Shimmer < 3.0%, HNR > 20dB. "
                    "반드시 '이 결과는 참고용이며, 정확한 진단은 전문 의료진 상담이 필요합니다'를 포함하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"다음 음성 분석 결과를 해석해주세요:\n"
                    f"- 기본 주파수(F0): {features['f0_mean']:.1f} Hz (표준편차: {features['f0_std']:.1f})\n"
                    f"- Jitter (주파수 변동률): {features['jitter']:.4f}%\n"
                    f"- Shimmer (진폭 변동률): {features['shimmer']:.4f}%\n"
                    f"- HNR (조음대잡음비): {features['hnr']:.2f} dB\n"
                    f"- 녹음 길이: {features['duration']:.1f}초\n"
                    f"- 위험도 판단: {features['risk_level']}"
                ),
            },
        ]
        return self._call_api(messages)

    def record_audio(self, duration=5, sr=22050, callback=None):
        """마이크로 음성 녹음"""
        def _run():
            try:
                import sounddevice as sd
                import soundfile as sf

                audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
                sd.wait()

                # 파일 저장
                filename = f"voice_{int(datetime.now().timestamp())}.wav"
                filepath = os.path.join(MEDIA_DIR, filename)
                sf.write(filepath, audio, sr)

                result = {"path": filepath, "status": "success"}
            except Exception as e:
                result = {"path": None, "status": "error", "error": str(e)}

            if callback:
                callback(result)
            return result

        from datetime import datetime

        if callback:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return None
        else:
            return _run()
