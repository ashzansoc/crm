<template>
  <div class="flex h-full bg-surface-white">
    <!-- Sidebar -->
    <div class="flex w-64 flex-col border-r bg-surface-gray-2">
      <div class="p-4">
        <Button variant="solid" class="w-full justify-center" @click="startNewChat">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          New Chat
        </Button>
      </div>
      
      <div class="flex-1 overflow-y-auto px-2">
        <div v-if="loadingHistory" class="p-4 text-center text-sm text-ink-gray-5">
          Loading history...
        </div>
        <div v-else-if="chatHistory.length === 0" class="p-4 text-center text-sm text-ink-gray-5">
          No chat history
        </div>
        <div v-else class="flex flex-col gap-1">
          <button
            v-for="chat in chatHistory"
            :key="chat.name"
            class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-gray-3"
            :class="currentChatId === chat.name ? 'bg-surface-gray-3 font-medium text-ink-gray-9' : 'text-ink-gray-7'"
            @click="loadChat(chat.name)"
          >
            <FeatherIcon name="message-square" class="h-4 w-4 flex-shrink-0" />
            <span class="truncate">{{ chat.title }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="flex flex-1 flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between border-b px-5 py-3">
        <h1 class="text-xl font-semibold text-ink-gray-9">
          {{ currentChatTitle || 'New Chat' }}
        </h1>
      </div>

      <!-- Chat Messages -->
      <div class="flex-1 overflow-y-auto p-4" ref="chatContainer">
        <div v-if="messages.length === 0" class="flex h-full items-center justify-center text-ink-gray-4">
          <div class="text-center">
            <SparkleIcon class="mx-auto h-12 w-12 text-ink-gray-3" />
            <p class="mt-2">Start a conversation with AI</p>
          </div>
        </div>
        
        <div v-else class="flex flex-col gap-4">
          <div
            v-for="message in messages"
            :key="message.id"
            class="flex w-full gap-3"
            :class="message.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
          >
            <!-- Avatar -->
            <div class="flex-shrink-0">
              <UserAvatar
                v-if="message.role === 'user'"
                :user="user"
                size="md"
              />
              <div
                v-else
                class="flex h-8 w-8 items-center justify-center rounded-full bg-surface-gray-6"
              >
                <SparkleIcon class="h-4 w-4 text-ink-gray-7" />
              </div>
            </div>

            <!-- Message Bubble -->
            <div
              class="max-w-[70%] rounded-lg px-4 py-2 text-base"
              :class="
                message.role === 'user'
                  ? 'bg-surface-gray-9 text-ink-white'
                  : 'bg-surface-gray-2 text-ink-gray-9'
              "
            >
              <div class="whitespace-pre-wrap">{{ message.content }}</div>
            </div>
          </div>
          
          <!-- Typing Indicator -->
          <div v-if="isTyping" class="flex w-full gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-surface-gray-6">
              <SparkleIcon class="h-4 w-4 text-ink-gray-7" />
            </div>
            <div class="flex items-center rounded-lg bg-surface-gray-2 px-4 py-2">
              <div class="flex gap-1">
                <div class="h-2 w-2 animate-bounce rounded-full bg-ink-gray-5" style="animation-delay: 0ms"></div>
                <div class="h-2 w-2 animate-bounce rounded-full bg-ink-gray-5" style="animation-delay: 150ms"></div>
                <div class="h-2 w-2 animate-bounce rounded-full bg-ink-gray-5" style="animation-delay: 300ms"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="border-t p-4">
        <div class="flex gap-2">
          <textarea
            v-model="newMessage"
            @keydown.enter.prevent="sendMessage"
            placeholder="Type your message..."
            class="flex-1 resize-none rounded-lg border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-base focus:border-outline-gray-4 focus:outline-none focus:ring-0"
            rows="1"
            style="min-height: 42px; max-height: 120px"
          ></textarea>
          <Button
            variant="solid"
            :disabled="!newMessage.trim() || isTyping"
            @click="sendMessage"
          >
            <template #icon>
              <FeatherIcon name="send" class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <div class="mt-2 text-center text-xs text-ink-gray-4">
          AI can make mistakes. Consider checking important information.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { Button, FeatherIcon, call } from 'frappe-ui'
import UserAvatar from '@/components/UserAvatar.vue'
import SparkleIcon from '@/components/Icons/SparkleIcon.vue'
import { sessionStore } from '@/stores/session'

const { user } = sessionStore()
const chatContainer = ref(null)
const newMessage = ref('')
const isTyping = ref(false)
const messages = ref([])
const chatHistory = ref([])
const currentChatId = ref(null)
const loadingHistory = ref(false)

const currentChatTitle = computed(() => {
  if (!currentChatId.value) return 'New Chat'
  const chat = chatHistory.value.find(c => c.name === currentChatId.value)
  return chat ? chat.title : 'Chat'
})

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const fetchHistory = async () => {
  loadingHistory.value = true
  try {
    const result = await call('crm.api.ai.get_user_chat_history')
    chatHistory.value = result || []
  } catch (error) {
    console.error('Error fetching history:', error)
  } finally {
    loadingHistory.value = false
  }
}

const loadChat = async (chatId) => {
  if (currentChatId.value === chatId) return
  
  currentChatId.value = chatId
  messages.value = [] // Clear current messages
  
  try {
    const result = await call('crm.api.ai.get_chat_session', { name: chatId })
    if (result) {
      const parsedMessages = typeof result === 'string' ? JSON.parse(result) : result
      messages.value = parsedMessages.map((m, index) => ({
        id: index,
        role: m.role,
        content: m.content
      }))
      await scrollToBottom()
    }
  } catch (error) {
    console.error('Error loading chat:', error)
  }
}

const startNewChat = () => {
  currentChatId.value = null
  messages.value = []
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || isTyping.value) return

  const userContent = newMessage.value.trim()

  // Add user message locally
  const userMsg = {
    id: Date.now(),
    role: 'user',
    content: userContent
  }
  
  messages.value.push(userMsg)
  newMessage.value = ''
  await scrollToBottom()

  // Call AI API
  isTyping.value = true
  await scrollToBottom()

  try {
    const response = await call('crm.api.ai.chat', {
      message: userContent,
      chat_id: currentChatId.value
    })

    // Response contains { response: "...", chat_id: "..." }
    const aiContent = response.response
    const chatId = response.chat_id
    
    const aiMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: aiContent
    }
    messages.value.push(aiMsg)
    
    // If this was a new chat, update currentChatId and refresh history
    if (!currentChatId.value && chatId) {
      currentChatId.value = chatId
      await fetchHistory()
    }
  } catch (error) {
    console.error(error)
    const errorMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: "Sorry, I encountered an error. Please try again later."
    }
    messages.value.push(errorMsg)
  } finally {
    isTyping.value = false
    await scrollToBottom()
  }
}

onMounted(() => {
  fetchHistory()
})
</script>
