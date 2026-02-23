<template>
  <div class="flex flex-col h-full">
    <!-- Panel header -->
    <div class="px-4 py-4 border-b border-slate-700">
      <h2 class="text-sm font-semibold text-white">Frequently Asked</h2>
      <p class="text-xs text-slate-400 mt-0.5">
        Click a question to ask it
      </p>
    </div>

    <!-- FAQ list -->
    <div class="flex-1 overflow-y-auto py-2 scrollbar-thin">
      <!-- Loading skeleton -->
      <div v-if="!chatStore.faqsLoaded" class="px-4 py-3 space-y-3">
        <div
          v-for="n in 5"
          :key="n"
          class="h-4 bg-slate-700 rounded animate-pulse"
          :style="{ width: `${60 + n * 5}%` }"
        />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!chatStore.faqs.length"
        class="px-4 py-6 text-center text-slate-500 text-xs"
      >
        No FAQs found.<br />Run <code class="text-slate-400">manage.py seed_faq</code>
      </div>

      <!-- Category groups -->
      <div
        v-for="(questions, category) in chatStore.faqsByCategory"
        :key="category"
        class="mb-1"
      >
        <!-- Category heading -->
        <button
          class="w-full flex items-center justify-between px-4 py-2 text-left"
          @click="toggleCategory(category)"
        >
          <span
            class="text-xs font-semibold uppercase tracking-wider"
            :class="openCategories.has(category) ? 'text-indigo-400' : 'text-slate-400'"
          >
            {{ category }}
          </span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-3.5 h-3.5 text-slate-500 transition-transform"
            :class="openCategories.has(category) ? 'rotate-180' : ''"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        <!-- Question list for this category -->
        <Transition name="slide">
          <ul v-if="openCategories.has(category)" class="pb-1">
            <li
              v-for="faq in questions"
              :key="faq.id"
              class="px-4 py-1.5 cursor-pointer text-slate-300 hover:text-white hover:bg-slate-700/60 text-xs rounded transition-colors"
              @click="ask(faq.question)"
            >
              {{ faq.question }}
            </li>
          </ul>
        </Transition>
      </div>
    </div>

    <!-- Footer -->
    <div class="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
      {{ chatStore.faqs.length }} entries in knowledge base
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from "vue";
import { useChatStore } from "@/stores/chat.js";

const chatStore = useChatStore();

// Track which category accordions are open
const openCategories = reactive(new Set());

function toggleCategory(cat) {
  if (openCategories.has(cat)) {
    openCategories.delete(cat);
  } else {
    openCategories.add(cat);
  }
}

// Pre-fill the chat input by dispatching a custom event the ChatWindow listens to.
// We use the store action directly — clicking a FAQ sends it as a message.
function ask(question) {
  chatStore.sendMessage(question);
}

// Open the first category by default once FAQs load
onMounted(async () => {
  await chatStore.fetchFAQs();
  const firstCat = Object.keys(chatStore.faqsByCategory)[0];
  if (firstCat) openCategories.add(firstCat);
});
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition:
    max-height 0.2s ease,
    opacity 0.2s ease;
  overflow: hidden;
  max-height: 500px;
}
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
