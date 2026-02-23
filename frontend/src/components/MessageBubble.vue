<template>
  <div
    class="flex gap-3 items-end"
    :class="isUser ? 'flex-row-reverse' : 'flex-row'"
  >
    <!-- Avatar -->
    <div
      class="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow"
      :class="isUser ? 'bg-indigo-600 text-white' : 'bg-slate-600 text-slate-200'"
    >
      {{ isUser ? "You" : "AI" }}
    </div>

    <!-- Bubble + sources -->
    <div
      class="flex flex-col gap-2 max-w-[75%]"
      :class="isUser ? 'items-end' : 'items-start'"
    >
      <!-- Message bubble -->
      <div
        class="px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm"
        :class="
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm whitespace-pre-wrap'
            : 'bg-white text-slate-800 border border-slate-200 rounded-bl-sm prose prose-sm max-w-none'
        "
        v-html="isUser ? escapeHtml(message.content) : renderedMarkdown"
      />

      <!-- Sources dropdown — shown only for assistant messages -->
      <div
        v-if="!isUser && uniqueSources.length"
        class="w-full"
      >
        <button
          class="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors px-1 group"
          @click="sourcesOpen = !sourcesOpen"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-3 h-3 transition-transform"
            :class="sourcesOpen ? 'rotate-90' : ''"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          {{ uniqueSources.length }} source{{ uniqueSources.length > 1 ? 's' : '' }} consultée{{ uniqueSources.length > 1 ? 's' : '' }}
        </button>

        <Transition name="slide">
          <div v-if="sourcesOpen" class="mt-1.5 flex flex-col gap-1">
            <div
              v-for="(src, i) in uniqueSources"
              :key="i"
              class="flex items-start gap-2 px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700"
            >
              <span
                class="shrink-0 mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide bg-indigo-900 text-indigo-300"
              >
                {{ src.category }}
              </span>
              <span class="text-xs text-slate-300 leading-snug">{{ src.question }}</span>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Timestamp -->
      <span class="text-xs text-slate-500 px-1">{{ formattedTime }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { marked } from "marked";

const props = defineProps({
  message: {
    type: Object,
    required: true,
    // shape: { role, content, sources, timestamp }
  },
});

const isUser = computed(() => props.message.role === "user");
const sourcesOpen = ref(false);

// Render assistant markdown to HTML
const renderedMarkdown = computed(() => {
  if (isUser.value) return "";
  return marked.parse(props.message.content ?? "");
});

// Escape HTML for user messages (displayed as plain text via whitespace-pre-wrap)
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Deduplicate sources by question to avoid showing the same FAQ 3 times
const uniqueSources = computed(() => {
  const seen = new Set();
  return (props.message.sources ?? []).filter((src) => {
    if (seen.has(src.question)) return false;
    seen.add(src.question);
    return true;
  });
});

const formattedTime = computed(() => {
  const d = props.message.timestamp ? new Date(props.message.timestamp) : new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
});
</script>

<style scoped>
/* Sources dropdown transition */
.slide-enter-active,
.slide-leave-active {
  transition: max-height 0.2s ease, opacity 0.15s ease;
  overflow: hidden;
  max-height: 300px;
}
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Prose styles for markdown content inside the assistant bubble */
:deep(.prose) {
  color: #1e293b;
}
:deep(.prose p) {
  margin: 0 0 0.5em;
}
:deep(.prose p:last-child) {
  margin-bottom: 0;
}
:deep(.prose strong) {
  font-weight: 600;
  color: #0f172a;
}
:deep(.prose ol),
:deep(.prose ul) {
  margin: 0.4em 0 0.4em 1.2em;
  padding: 0;
}
:deep(.prose li) {
  margin-bottom: 0.25em;
}
:deep(.prose code) {
  background: #f1f5f9;
  padding: 0.1em 0.3em;
  border-radius: 4px;
  font-size: 0.85em;
}
</style>
