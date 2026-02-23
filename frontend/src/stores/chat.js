/**
 * Pinia store — global state for the chat feature.
 *
 * Pinia is Vue 3's official state-management library.
 * A "store" is a reactive singleton that any component can import and use.
 *
 * This store owns:
 *   - the list of messages in the current session
 *   - the session ID (so the backend can group turns into one conversation)
 *   - loading / error state
 *   - the FAQ catalogue (fetched once from the API)
 */

import axios from "axios";
import { defineStore } from "pinia";

// When using the Vite dev proxy, relative paths (/api/…) are enough.
// In production or Docker, set VITE_API_URL so axios knows the full host.
const API_BASE = import.meta.env.VITE_API_URL ?? "";

export const useChatStore = defineStore("chat", {
  state: () => ({
    /** @type {{ role: string, content: string, sources: any[], timestamp: Date }[]} */
    messages: [],
    /** UUID assigned by the backend for this session */
    sessionId: null,
    isLoading: false,
    /** Human-readable error message, null when no error */
    error: null,
    /** @type {{ id: string, question: string, answer: string, category: string }[]} */
    faqs: [],
    faqsLoaded: false,
  }),

  getters: {
    /** FAQs grouped by category → { account: [...], billing: [...] } */
    faqsByCategory: (state) => {
      return state.faqs.reduce((groups, faq) => {
        const cat = faq.category || "general";
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(faq);
        return groups;
      }, {});
    },

    hasMessages: (state) => state.messages.length > 0,
  },

  actions: {
    /**
     * Send a user message to the backend and append both the user turn
     * and the AI response to the messages list.
     */
    async sendMessage(content) {
      if (!content.trim() || this.isLoading) return;

      // Optimistically append the user message
      this.messages.push({
        role: "user",
        content: content.trim(),
        sources: [],
        timestamp: new Date(),
      });
      this.isLoading = true;
      this.error = null;

      try {
        const { data } = await axios.post(`${API_BASE}/api/chat/`, {
          message: content.trim(),
          session_id: this.sessionId,
        });

        this.sessionId = data.session_id;

        this.messages.push({
          role: "assistant",
          content: data.answer,
          sources: data.sources ?? [],
          timestamp: new Date(),
        });
      } catch (err) {
        this.error =
          err.response?.data?.error ??
          err.message ??
          "Could not reach the assistant. Is the backend running?";
      } finally {
        this.isLoading = false;
      }
    },

    /** Load the FAQ catalogue (called once on page load). */
    async fetchFAQs() {
      if (this.faqsLoaded) return;
      try {
        const { data } = await axios.get(`${API_BASE}/api/faq/`);
        this.faqs = data;
        this.faqsLoaded = true;
      } catch {
        // Non-critical — the FAQ panel just won't show
      }
    },

    /** Reset the current conversation (keeps FAQ data intact). */
    clearConversation() {
      this.messages = [];
      this.sessionId = null;
      this.error = null;
    },
  },
});
