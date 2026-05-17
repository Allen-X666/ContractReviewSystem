import { get, put, del, post } from '@/utils/request'
import { SecureStorage } from '@/utils/secureStorage'

export function getConversationList(params) {
  return get('/chatbot/conversations', params)
}

export function getConversationDetail(id, params) {
  return get(`/chatbot/conversations/${id}`, params)
}

export function renameConversation(id, name) {
  return put(`/chatbot/conversations/${id}/name`, { name })
}

export function deleteConversation(id) {
  return del(`/chatbot/conversations/${id}`)
}

export function sendMessage(content, conversationId) {
  return post('/chatbot/messages', { content, conversationId })
}

/**
 * 流式发送消息（SSE）
 *
 * 使用 fetch + ReadableStream 接收 SSE 流式响应。
 * EventSource 仅支持 GET，而发送消息需 POST，故采用此方案。
 *
 * @param {Object} params - 消息参数
 * @param {number} params.conversationId - 对话ID
 * @param {string} params.content - 消息内容
 * @param {Function} params.onToken - 每收到一个 token 时的回调
 * @param {Function} params.onDone - 流式输出完成时的回调
 * @param {Function} params.onError - 发生错误时的回调
 * @returns {AbortController} 用于取消请求的控制器
 */
export function sendMessageStream({ conversationId, content, onToken, onDone, onError, onConversationId }) {
  const controller = new AbortController()

  const token = SecureStorage.getToken() || ''
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

  fetch(`${baseURL}/chatbot/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({ conversationId, content }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text()
        onError?.(new Error(`HTTP ${response.status}: ${errorText}`))
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let conversationIdReceived = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()

            if (data === '[DONE]') {
              onDone?.()
              return
            }

            try {
              const parsed = JSON.parse(data)
              if (parsed.error) {
                onError?.(new Error(parsed.error))
                return
              }
              // 处理后端返回的 conversationId
              if (parsed.conversationId && !conversationIdReceived) {
                onConversationId?.(parsed.conversationId)
                conversationIdReceived = true
                continue
              }
              if (parsed.content) {
                let textParts = ''
                if (Array.isArray(parsed.content)) {
                  textParts = parsed.content.map(item => {
                    if (typeof item === 'string') return item
                    if (item && typeof item === 'object' && item.text) return item.text
                    return ''
                  }).join('')
                } else if (typeof parsed.content === 'object' && parsed.content.text) {
                  // 处理单个对象格式 {'text': 'xxx'}
                  textParts = parsed.content.text
                } else {
                  textParts = String(parsed.content)
                }
                if (textParts) {
                  onToken(textParts)
                }
              }
            } catch {
              // 非 JSON 数据，忽略
            }
          }
        }
      }

      onDone?.()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

  return controller
}

/**
 * 导出对话记录为 Excel 文件
 *
 * @param {number} conversationId - 对话ID
 * @returns {Promise<void>}
 */
export async function exportConversation(conversationId) {
  const token = SecureStorage.getToken() || ''
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

  const response = await fetch(`${baseURL}/chatbot/conversations/${conversationId}/export`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`导出失败: HTTP ${response.status}`)
  }

  // 从响应头中提取文件名
  const contentDisposition = response.headers.get('Content-Disposition')
  let fileName = '对话记录.xlsx'

  if (contentDisposition) {
    // 尝试匹配 filename*=utf-8'' 格式
    const utf8Match = contentDisposition.match(/filename\*=utf-8''(.+?)(?:;|$)/)
    if (utf8Match) {
      fileName = decodeURIComponent(utf8Match[1])
    } else {
      // 尝试匹配 filename="xxx" 格式
      const filenameMatch = contentDisposition.match(/filename="(.+?)"/)
      if (filenameMatch) {
        fileName = filenameMatch[1]
      }
    }
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
