export interface User {
  id: number;
  email: string;
  full_name: string | null;
  credits: number;
  plan: string;
  xp: number;
  level: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export interface Message {
  id?: number;
  role: 'user' | 'agent' | 'system';
  agent_name?: string;
  content: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

export interface Conversation {
  id: number;
  title: string | null;
  agent_type: string;
  status: string;
  created_at: string;
  messages: Message[];
}

export interface Report {
  id: number;
  report_uuid: string;
  task_type: string;
  title: string | null;
  final_content: string;
  agents_used: string[] | null;
  created_at: string;
}

export interface Plan {
  id: string;
  name: string;
  credits: number;
  price: number;
  features: string[];
}
