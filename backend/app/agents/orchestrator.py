"""Orchestrator Agent - coordinates multiple agents for complex tasks."""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, field

from app.agents.base import BaseAgent, AgentResponse
from app.agents.strategic import StrategicAgent
from app.agents.marketing import MarketingAgent
from app.agents.competitor import CompetitorAgent
from app.agents.content import ContentAgent
from app.agents.social import SocialMediaAgent
from app.agents.auditor import AuditorAgent

logger = logging.getLogger(__name__)


@dataclass
class TaskPlan:
    """Execution plan for a complex task."""
    primary_agent: str
    supporting_agents: List[str] = field(default_factory=list)
    needs_audit: bool = True
    description: str = ""


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"
    description = "منسق الوكلاء - يحلل المهمة ويوزعها على الوكلاء المناسبين"
    icon = "🎯"
    color = "#667eea"

    def __init__(self):
        super().__init__()
        self.agents: Dict[str, BaseAgent] = {
            "strategic": StrategicAgent(),
            "marketing": MarketingAgent(),
            "competitor": CompetitorAgent(),
            "content": ContentAgent(),
            "social": SocialMediaAgent(),
            "auditor": AuditorAgent(),
        }

    async def _analyze_task(self, user_input: str) -> TaskPlan:
        """Analyze user input and determine which agents to invoke."""
        system = (
            "أنت منسق ذكي لوكلاء AI. حلل طلب المستخدم وحدد أي وكلاء مطلوبون. "
            "أجب بـ JSON فقط: {\"primary\": "...", "supporting": ["..."], "audit": true/false}"
        )

        prompt = f"""حلل الطلب التالي وحدد الوكلاء المطلوبين:

الطلب: "{user_input[:500]}"

الوكلاء المتاحون:
- strategic: تحليل استراتيجي وSWOT
- marketing: حملات تسويقية
- competitor: تحليل منافسين
- content: إنشاء محتوى رقمي
- social: منشورات سوشيال ميديا
- auditor: مراجعة جودة

أجب بـ JSON فقط."""

        try:
            result = await self._generate(system, prompt, temp=0.1, max_tokens=500)
            # Simple parsing (in production use proper JSON parsing)
            if "strategic" in user_input.lower() or "خطة" in user_input or "swot" in user_input.lower():
                return TaskPlan("strategic", ["auditor"], True, "تحليل استراتيجي")
            elif "تسويق" in user_input or "marketing" in user_input.lower() or "حملة" in user_input:
                return TaskPlan("marketing", ["social", "auditor"], True, "حملة تسويقية")
            elif "منافس" in user_input or "competitor" in user_input.lower():
                return TaskPlan("competitor", ["strategic", "auditor"], True, "تحليل منافسين")
            elif "محتوى" in user_input or "كتاب" in user_input or "content" in user_input.lower():
                return TaskPlan("content", ["marketing", "social", "auditor"], True, "إنشاء محتوى")
            elif "سوشيال" in user_input or "منشور" in user_input or "social" in user_input.lower():
                return TaskPlan("social", ["auditor"], True, "منشورات سوشيال")
            else:
                return TaskPlan("strategic", ["auditor"], True, "تحليل عام")
        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            return TaskPlan("strategic", ["auditor"], True, "تحليل افتراضي")

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Main entry point - orchestrates multi-agent workflow."""

        # Step 1: Analyze task
        plan = await self._analyze_task(user_input)
        logger.info(f"Task plan: {plan}")

        # Step 2: Execute primary agent
        primary_agent = self.agents.get(plan.primary_agent)
        if not primary_agent:
            return AgentResponse(
                content="عذراً، الوكيل المطلوب غير متاح.",
                agent_name=self.name,
                confidence=0.0
            )

        primary_result = await primary_agent.process(user_input, context)

        # Step 3: Execute supporting agents in parallel
        supporting_results = []
        if plan.supporting_agents:
            tasks = []
            for agent_name in plan.supporting_agents:
                if agent_name in self.agents and agent_name != plan.primary_agent:
                    agent = self.agents[agent_name]
                    tasks.append(agent.process(user_input, {**context, "primary_result": primary_result.content}))

            if tasks:
                supporting_results = await asyncio.gather(*tasks, return_exceptions=True)
                supporting_results = [
                    r for r in supporting_results 
                    if not isinstance(r, Exception)
                ]

        # Step 4: Audit if needed
        final_content = primary_result.content
        if plan.needs_audit:
            auditor = self.agents["auditor"]
            combined = primary_result.content
            for sr in supporting_results:
                combined += f"\n\n--- {sr.agent_name} ---\n{sr.content}"

            audit_result = await auditor.process(combined, context)
            final_content = audit_result.content

        # Step 5: Build final response
        agents_used = [plan.primary_agent] + plan.supporting_agents

        header = f"🎯 **{plan.description}**\n\n"
        header += f"*تم تنفيذ المهمة بواسطة: {', '.join([self.agents[a].icon + ' ' + self.agents[a].description for a in agents_used if a in self.agents])}*\n\n"
        header += "---\n\n"

        return AgentResponse(
            content=header + final_content,
            agent_name=self.name,
            confidence=primary_result.confidence,
            metadata={
                "type": "orchestrated",
                "plan": plan,
                "agents_used": agents_used,
                "supporting_results": len(supporting_results)
            }
        )

    async def chat_with_agent(self, agent_name: str, message: str, history: Optional[List[Dict]] = None) -> AgentResponse:
        """Direct chat with a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return AgentResponse(
                content=f"الوكيل '{agent_name}' غير موجود. الوكلاء المتاحون: {', '.join(self.agents.keys())}",
                agent_name=self.name,
                confidence=0.0
            )
        return await agent.chat(message, history)

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Return list of available agents with metadata."""
        return [
            {
                "id": name,
                "name": agent.name,
                "description": agent.description,
                "icon": agent.icon,
                "color": agent.color
            }
            for name, agent in self.agents.items()
        ]


# Singleton
orchestrator = OrchestratorAgent()
