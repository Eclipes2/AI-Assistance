<template>
  <div class="flex h-screen bg-slate-900 overflow-hidden">
    <!-- ── Main: Chat area ───────────────────────────────── -->
    <main class="flex flex-col flex-1 min-w-0">
      <!-- Top bar -->
      <header
        class="flex items-center justify-between px-6 py-3 bg-slate-800 border-b border-slate-700"
      >
        <div class="flex items-center gap-3">
          <!-- Logo mark -->
          <div
            class="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center shadow"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="w-5 h-5 text-white"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                d="M12 2C6.477 2 2 6.477 2 12c0 1.89.525 3.66 1.438 5.168L2 22l4.832-1.438A9.956 9.956 0 0 0 12 22c5.523 0 10-4.477 10-10S17.523 2 12 2z"
              />
            </svg>
          </div>
          <div>
            <h1 class="font-semibold text-white text-sm">AI Support Chat</h1>
            <p class="text-xs text-green-400 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
              Online · Powered by Mistral
            </p>
          </div>
        </div>

        <button
          class="text-slate-400 hover:text-white transition-colors p-1 rounded"
          title="New conversation"
          @click="chatStore.clearConversation()"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 4v16m8-8H4"
            />
          </svg>
        </button>
      </header>

      <!-- Chat window fills remaining height -->
      <ChatWindow class="flex-1 min-h-0" />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import ChatWindow from "@/components/ChatWindow.vue";
import { useChatStore } from "@/stores/chat.js";

const chatStore = useChatStore();

onMounted(() => {
  chatStore.fetchFAQs();
});
</script>
