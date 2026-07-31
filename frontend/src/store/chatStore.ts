import { create } from 'zustand';
import type { Message, Conversation, Agent } from '@/types';

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  selectedAgent: string | null;
  isTyping: boolean;
  agents: Agent[];
  setAgents: (agents: Agent[]) => void;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conv: Conversation | null) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setSelectedAgent: (agent: string | null) => void;
  setIsTyping: (typing: boolean) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  selectedAgent: null,
  isTyping: false,
  agents: [],
  setAgents: (agents) => set({ agents }),
  setConversations: (conversations) => set({ conversations }),
  setCurrentConversation: (conv) => set({ currentConversation: conv, messages: conv?.messages || [] }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  setIsTyping: (typing) => set({ isTyping: typing }),
  clearChat: () => set({ currentConversation: null, messages: [], selectedAgent: null }),
}));
