import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as chatbotApi from '@/api/chatbot'

const BUTTON_POS_KEY = 'chatbot_button_position'
const CONVERSATION_ID_COUNTER_KEY = 'chatbot_conversation_id_counter'

let activeStreamController = null

function loadButtonPosition() {
  // 刷新页面后强制重置位置到右下角
  return null
}

function saveButtonPosition(pos) {
  // 不保存位置，刷新页面后重置到右下角
  // sessionStorage.setItem(BUTTON_POS_KEY, JSON.stringify(pos))
}

function getNextConversationId() {
  const current = parseInt(localStorage.getItem(CONVERSATION_ID_COUNTER_KEY) || '0', 10)
  const next = current + 1
  localStorage.setItem(CONVERSATION_ID_COUNTER_KEY, next.toString())
  return next
}

function toTimestamp(dateStr) {
  if (!dateStr) return Date.now()
  if (typeof dateStr === 'number') return dateStr
  return new Date(dateStr).getTime()
}

function normalizeMessage(msg) {
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: toTimestamp(msg.createdAt)
  }
}

function normalizeConversationSummary(item) {
  return {
    id: item.id,
    name: item.name,
    messageCount: item.messageCount ?? 0,
    lastMessage: item.lastMessage ?? '',
    createdAt: toTimestamp(item.createdAt),
    updatedAt: toTimestamp(item.updatedAt),
    messages: []
  }
}

function normalizeConversationDetail(detail) {
  return {
    id: detail.id,
    name: detail.name,
    createdAt: toTimestamp(detail.createdAt),
    updatedAt: toTimestamp(detail.updatedAt),
    messages: (detail.messages || []).map(normalizeMessage)
  }
}

export const useChatbotStore = defineStore('chatbot', () => {
  const conversations = ref([])
  const currentConversationId = ref(null)
  const currentConversationClientId = ref(null)
  const buttonPosition = ref(loadButtonPosition())
  const loading = ref(false)
  const sending = ref(false)

  const currentConversation = computed(() => {
    const targetId = currentConversationId.value || currentConversationClientId.value
    if (!targetId) return null
    return conversations.value.find(c => c.id === targetId) || null
  })

  const sortedConversations = computed(() => {
    return [...conversations.value].sort((a, b) => b.updatedAt - a.updatedAt)
  })

  async function loadConversations() {
    try {
      loading.value = true
      const res = await chatbotApi.getConversationList()
      const list = res.data || []
      conversations.value = list.map(normalizeConversationSummary)
    } catch {
      conversations.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadConversationDetail(id) {
    const res = await chatbotApi.getConversationDetail(id)
    const detail = normalizeConversationDetail(res.data)
    const idx = conversations.value.findIndex(c => c.id === id)
    if (idx !== -1) {
      conversations.value[idx].messages = detail.messages
      conversations.value[idx].name = detail.name
      conversations.value[idx].updatedAt = detail.updatedAt
    }
    return detail
  }

  function sendMessage(content) {
    return new Promise((resolve, reject) => {
      sending.value = true

      const now = Date.now()
      // 使用后端返回的ID或临时客户端ID
      const clientId = currentConversationId.value || currentConversationClientId.value
      
      // 如果是首次发送（没有后端ID也没有客户端ID），不传递conversationId
      const isFirstMessage = !currentConversationId.value && !currentConversationClientId.value

      const userMsg = {
        id: `user-${now}`,
        role: 'user',
        content,
        timestamp: now,
      }

      const assistantMsg = {
        id: `assistant-${now}`,
        role: 'assistant',
        content: '',
        timestamp: now,
      }

      // 使用临时ID管理本地对话状态
      const tempId = clientId || `temp-${now}`
      let conv = conversations.value.find(c => c.id === tempId)
      if (!conv) {
        conv = {
          id: tempId,
          name: '新对话',
          messages: [],
          createdAt: now,
          updatedAt: now,
        }
        conversations.value.unshift(conv)
      }
      // 设置当前对话的临时ID，确保消息能立即显示
      currentConversationClientId.value = tempId
      conv.messages.push(userMsg, assistantMsg)

      activeStreamController = chatbotApi.sendMessageStream({
        conversationId: isFirstMessage ? null : currentConversationId.value,
        content,
        onToken(token) {
          assistantMsg.content += token
          conv.updatedAt = Date.now()
        },
        onConversationId(serverId) {
          // 收到后端返回的 conversationId，更新本地状态
          if (serverId) {
            const oldTempId = conv.id
            currentConversationId.value = serverId
            // 更新对话ID
            conv.id = serverId
            // 如果对话列表中有临时ID的对话，更新它
            const existingConv = conversations.value.find(c => c.id === oldTempId)
            if (existingConv) {
              existingConv.id = serverId
            }
            log.info(`收到后端 conversationId: ${serverId}, 更新本地临时ID: ${oldTempId}`)
          }
        },
        onDone() {
          sending.value = false
          activeStreamController = null
          resolve({ userMsg, assistantMsg })
        },
        onError(err) {
          sending.value = false
          activeStreamController = null
          if (assistantMsg.content) {
            assistantMsg.content += '\n\n*（回答中断）*'
          } else {
            assistantMsg.content = '抱歉，回答出现问题，请稍后重试。'
          }
          reject(err)
        },
      })
    })
  }

  function cancelStream() {
    if (activeStreamController) {
      activeStreamController.abort()
      activeStreamController = null
      sending.value = false
    }
  }

  async function switchConversation(id) {
    currentConversationId.value = id
    const conv = conversations.value.find(c => c.id === id)
    if (conv && conv.messages.length === 0) {
      await loadConversationDetail(id)
    }
  }

  function newChat() {
    // 点击创建新对话后，清空ID，下次发送消息时id为null
    currentConversationId.value = null
    currentConversationClientId.value = null
  }

  async function renameConversation(id, newName) {
    await chatbotApi.renameConversation(id, newName)
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      conv.name = newName
    }
  }

  async function deleteConversation(id) {
    await chatbotApi.deleteConversation(id)
    const idx = conversations.value.findIndex(c => c.id === id)
    if (idx !== -1) {
      conversations.value.splice(idx, 1)
      if (currentConversationId.value === id) {
        currentConversationId.value = null
      }
    }
  }

  function updateButtonPosition(pos) {
    buttonPosition.value = pos
    saveButtonPosition(pos)
  }

  async function exportConversationToExcel(conversation) {
    const target = conversation || currentConversation.value
    if (!target || !target.id) return false

    try {
      await chatbotApi.exportConversation(target.id)
      return true
    } catch {
      return false
    }
  }

  return {
    conversations,
    currentConversationId,
    currentConversationClientId,
    currentConversation,
    sortedConversations,
    buttonPosition,
    loading,
    sending,
    loadConversations,
    loadConversationDetail,
    sendMessage,
    cancelStream,
    switchConversation,
    newChat,
    renameConversation,
    deleteConversation,
    updateButtonPosition,
    exportConversationToExcel
  }
})
