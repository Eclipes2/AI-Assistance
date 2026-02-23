<template>
  <div class="flex flex-col h-full bg-slate-900">
    <!-- ── Message list ──────────────────────────────────── -->
    <div
      ref="listRef"
      class="flex-1 overflow-y-auto px-4 py-6 space-y-5 scrollbar-thin"
    >
      <!-- Welcome screen (shown when no messages) -->
      <div
        v-if="!chatStore.hasMessages"
        class="flex flex-col items-center justify-center h-full text-center px-8"
      >
        <div
          class="w-16 h-16 rounded-full bg-indigo-600 flex items-center justify-center mb-4 shadow-lg"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-8 h-8 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-4 4z"
            />
          </svg>
        </div>
        <h2 class="text-white font-semibold text-lg mb-1">
          How can I help you today?
        </h2>
        <p class="text-slate-400 text-sm max-w-xs">
          Ask me anything about your account, billing, or technical issues. I'll
          look it up for you instantly.
        </p>

        <!-- Quick-start prompts -->
        <div class="flex flex-wrap gap-2 justify-center mt-6">
          <button
            v-for="prompt in quickPrompts"
            :key="prompt"
            class="px-3 py-1.5 text-xs text-slate-300 bg-slate-700 hover:bg-slate-600 rounded-full transition-colors border border-slate-600"
            @click="send(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
      </div>

      <!-- Actual messages -->
      <MessageBubble
        v-for="(msg, idx) in chatStore.messages"
        :key="idx"
        :message="msg"
      />

      <!-- Typing indicator -->
      <div v-if="chatStore.isLoading" class="flex gap-3 items-end">
        <div
          class="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-bold text-slate-200 shrink-0"
        >
          AI
        </div>
        <div
          class="px-4 py-3 bg-white border border-slate-200 rounded-2xl rounded-bl-sm shadow-sm flex gap-1.5"
        >
          <span
            class="w-2 h-2 rounded-full bg-slate-400 animate-bounce"
            style="animation-delay: 0ms"
          />
          <span
            class="w-2 h-2 rounded-full bg-slate-400 animate-bounce"
            style="animation-delay: 150ms"
          />
          <span
            class="w-2 h-2 rounded-full bg-slate-400 animate-bounce"
            style="animation-delay: 300ms"
          />
        </div>
      </div>
    </div>

    <!-- ── Error banner ──────────────────────────────────── -->
    <Transition name="fade">
      <div
        v-if="chatStore.error"
        class="mx-4 mb-2 px-4 py-2.5 bg-red-900/60 border border-red-700 text-red-300 text-sm rounded-lg flex items-start gap-2"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-4 h-4 mt-0.5 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
          />
        </svg>
        {{ chatStore.error }}
      </div>
    </Transition>

    <!-- ── Input bar ─────────────────────────────────────── -->
    <div
      class="px-4 pb-4 pt-2 bg-slate-800 border-t border-slate-700"
    >
      <form
        class="flex gap-2 items-end"
        @submit.prevent="send(inputText)"
      >
        <textarea
          ref="inputRef"
          v-model="inputText"
          rows="1"
          placeholder="Type your question…"
          class="flex-1 resize-none rounded-2xl px-4 py-2.5 text-sm bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent leading-snug max-h-32 scrollbar-thin"
          :disabled="chatStore.isLoading"
          @keydown.enter.exact.prevent="send(inputText)"
          @input="autoResize"
        />
        <button
          type="submit"
          :disabled="!inputText.trim() || chatStore.isLoading"
          class="shrink-0 w-10 h-10 rounded-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors shadow"
          title="Send (Enter)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-4 h-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 19V5m-7 7l7-7 7 7"
            />
          </svg>
        </button>
      </form>
      <p class="text-xs text-slate-500 mt-1.5 text-center">
        Press <kbd class="bg-slate-700 px-1 rounded text-slate-400">Enter</kbd>
        to send · <kbd class="bg-slate-700 px-1 rounded text-slate-400">Shift+Enter</kbd> for new line
      </p>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import MessageBubble from "./MessageBubble.vue";
import { useChatStore } from "@/stores/chat.js";

const chatStore = useChatStore();

const inputText = ref("");
const listRef = ref(null);
const inputRef = ref(null);

const quickPrompts = [
  "How do I reset my password?",
  "How can I cancel my subscription?",
  "What payment methods do you accept?",
  "Is my data secure?",
];

async function send(text) {
  if (!text.trim() || chatStore.isLoading) return;
  inputText.value = "";
  await nextTick();
  if (inputRef.value) {
    inputRef.value.style.height = "auto";
  }
  await chatStore.sendMessage(text);
}

// Auto-scroll to the latest message whenever messages change
watch(
  () => chatStore.messages.length,
  async () => {
    await nextTick();
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight;
    }
  }
);

// Also scroll when the loading indicator appears
watch(
  () => chatStore.isLoading,
  async () => {
    await nextTick();
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight;
    }
  }
);

// Auto-resize the textarea as the user types
function autoResize(e) {
  const el = e.target;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 128) + "px";
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
