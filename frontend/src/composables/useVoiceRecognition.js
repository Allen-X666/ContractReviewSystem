import { ref, computed, onBeforeUnmount } from 'vue'

const SpeechRecognition =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null

export function useVoiceRecognition(options = {}) {
  const {
    lang = 'zh-CN',
    continuous = true,   // 启用连续识别，边说边转换
    interimResults = true, // 启用临时结果，实时显示
    maxAlternatives = 1,
  } = options

  const isSupported = !!SpeechRecognition
  const isListening = ref(false)
  const isPaused = ref(false)
  const interimText = ref('')
  const finalText = ref('')
  const error = ref(null)
  const volume = ref(0)

  let recognition = null
  let audioContext = null
  let analyser = null
  let mediaStream = null
  let animFrameId = null
  let restartTimer = null
  let stoppedByUser = false

  const statusText = computed(() => {
    if (error.value) return '识别出错'
    if (isListening.value && isPaused.value) return '已暂停'
    if (isListening.value) return '正在聆听...'
    return '未开始'
  })

  function createRecognition() {
    if (!SpeechRecognition) return null

    const rec = new SpeechRecognition()
    rec.lang = lang
    rec.continuous = continuous
    rec.interimResults = interimResults
    rec.maxAlternatives = maxAlternatives

    rec.onstart = () => {
      isListening.value = true
      error.value = null
    }

    rec.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          final += transcript
        } else {
          interim += transcript
        }
      }
      if (final) {
        finalText.value += final
      }
      interimText.value = interim
    }

    rec.onerror = (event) => {
      if (event.error === 'no-speech') {
        return
      }
      if (event.error === 'aborted') {
        return
      }
      const errorMap = {
        'not-allowed': '麦克风权限被拒绝，请在浏览器设置中允许麦克风访问',
        'network': '网络错误，请检查网络连接或尝试使用 Chrome/Edge 浏览器',
        'audio-capture': '未检测到麦克风设备',
        'service-not-allowed': '语音识别服务不可用',
      }
      error.value = errorMap[event.error] || `语音识别错误: ${event.error}`
      isListening.value = false

      // network 错误时尝试重新创建 recognition 实例
      if (event.error === 'network') {
        recognition = null
      }
    }

    rec.onend = () => {
      // continuous=true 时，自动重启以继续识别
      if (isListening.value && !stoppedByUser && !isPaused.value) {
        restartTimer = setTimeout(() => {
          try {
            rec.start()
          } catch {
            isListening.value = false
          }
        }, 100)
      } else {
        isListening.value = false
      }
    }

    return rec
  }

  async function startVolumeMonitor() {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioContext = new (window.AudioContext || window.webkitAudioContext)()
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      const source = audioContext.createMediaStreamSource(mediaStream)
      source.connect(analyser)

      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      function updateVolume() {
        if (!analyser) return
        analyser.getByteFrequencyData(dataArray)
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i]
        }
        volume.value = sum / dataArray.length / 255
        animFrameId = requestAnimationFrame(updateVolume)
      }
      updateVolume()
    } catch {
      volume.value = 0
    }
  }

  function stopVolumeMonitor() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId)
      animFrameId = null
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop())
      mediaStream = null
    }
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close()
      audioContext = null
      analyser = null
    }
    volume.value = 0
  }

  async function start() {
    if (!isSupported) {
      error.value = '当前浏览器不支持语音识别功能'
      return
    }

    error.value = null
    interimText.value = ''
    finalText.value = ''
    stoppedByUser = false
    isPaused.value = false

    if (!recognition) {
      recognition = createRecognition()
    }

    try {
      await startVolumeMonitor()
      recognition.start()
    } catch (e) {
      if (e.name === 'InvalidStateError') {
        recognition.stop()
        setTimeout(() => {
          try {
            recognition.start()
          } catch {
            error.value = '语音识别启动失败，请重试'
          }
        }, 200)
      } else {
        error.value = '无法启动语音识别，请检查麦克风权限'
        stopVolumeMonitor()
      }
    }
  }

  function stop() {
    stoppedByUser = true
    isPaused.value = false
    if (restartTimer) {
      clearTimeout(restartTimer)
      restartTimer = null
    }
    if (recognition) {
      try {
        recognition.stop()
      } catch {
        // ignore
      }
    }
    stopVolumeMonitor()
    interimText.value = ''
  }

  function pause() {
    if (!isListening.value) return
    isPaused.value = true
    if (restartTimer) {
      clearTimeout(restartTimer)
      restartTimer = null
    }
    if (recognition) {
      try {
        recognition.stop()
      } catch {
        // ignore
      }
    }
    stopVolumeMonitor()
  }

  async function resume() {
    if (!isPaused.value) return
    isPaused.value = false
    stoppedByUser = false
    
    // 如果 recognition 为 null，重新创建
    if (!recognition) {
      recognition = createRecognition()
    }
    
    if (!recognition) {
      error.value = '语音识别不可用'
      return
    }
    
    try {
      await startVolumeMonitor()
      recognition.start()
    } catch {
      error.value = '恢复语音识别失败'
    }
  }

  function toggle() {
    if (isListening.value && !isPaused.value) {
      pause()
    } else if (isPaused.value) {
      resume()
    } else {
      start()
    }
  }

  function consumeFinalText() {
    const text = finalText.value
    finalText.value = ''
    return text
  }

  onBeforeUnmount(() => {
    stop()
    if (recognition) {
      recognition = null
    }
  })

  return {
    isSupported,
    isListening,
    isPaused,
    interimText,
    finalText,
    error,
    volume,
    statusText,
    start,
    stop,
    pause,
    resume,
    toggle,
    consumeFinalText,
  }
}
