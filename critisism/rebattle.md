1. Summary *

Please briefly summarize the main claims/contributions of the submission in your own words. (Please do not include your evaluation of the paper here).
Answer: This paper introduces an approach for safe multi-agent model-based reinforcement learning (RL). There is existing work on safe model-based RL as well as safe multi-agent RL; the novelty of this paper lies in bridging the gap between these two directions, which leads to improved performance over the baseline (i.e., safe multi-agent RL). The proposed framework is evaluated on SMAC, a standard multi-agent RL benchmark environment, showing significant improvement over the baseline in terms of maximizing rewards and minimizing safety-violation costs.
2. Strengths *

What are the main strengths of the submission? Please focus on novelty (how novel are the concepts, problems addressed, or methods introduced in the submission), soundness (is the submission technically sound), clarity (is the submission well-organized and
clearly written), and significance (comment on the likely impact the submission may have on the AI research community as a whole or on its own sub-field).
Answer: * The paper considers an important problem safe multi-agent RL, which has many real-world applications (e.g., drone fleets, decentralized power grid). * The combination of safe and model-based RL seems to be novel, and it leads to significant improvements in practical experiments. * The paper includes an ablation study.
3. Weaknesses *

What are the weaknesses of the submission? Please focus on novelty, soundness, clarity, and significance.
Answer: * The proposed world model is very similar to MAMBA [Egorov and Shpilman, 2022]; the paper should make it clear what the key differences are compared to this existing approach (main difference seems to be the introduction of the predicted cost \hat{c}). * The problem definition and the description of the proposed approach (up to Section 3.2) make absolutely no mention of communication between the agents. Section 3.4 starts by stating that the proposed approach is a Decentralized Execution approach, but then suddenly, it says that there is all-to-all communication between the agents. This is a very strong assumption (error- and delay-free all-to-all communication) in practice, and it comes out of nowhere. This assumption should be stated upfront. * Also, it is not clear how the attention mechanism used for processing the information received from other agents is trained. The preceding subsections are supposed to describe the training process, but since they make no mention of communication, there is no explanation of how the attention is trained (Section 3.4 is supposed to describe execution, not training). * The presentation of the paper is unclear at several other points. Here are a few examples: - Figures 1 and 2 refer to z_t, but this notation is never introduced or used in the text. - It is not clear if the value functions are shared between the agents or not. In fact, the paper does not make it clear what (if anything) is shared by the agents. Are the agents trained independently (e.g., similar to IPPO)? The paper later states that the approach is CTDE, but it is not clear what is centralized (beyond having access to the ground-truth state). - In the loss formula (end of page 2), the observation is the ground-truth o_t^i, but the other variables (\hat{r} and \hat{c}) are sampled ones. During training, shouldn't these variables all be ground-truth? Is this a typo? In the same formula, \theta is presumably the parameters of the world model, but this is never stated. - Acronym RSSM is used without ever being introduced. - The main text never makes it clear how the three phases are scheduled (i.e., that they are repeated periodically after a certain number of episodes); this is only clarified in the appendix. * The introduction includes this sentence as a motivation: "However, standard RL relies on trial-and-error, posing unacceptable risks in safety-critical environments where a single violation can be catastrophic." This issue is not addressed by the proposed approach since it starts by collecting experiences with the untrained policy, which could easily lead to violations. * It would help if the experiments included at least another benchmark (e.g., MPE, MaMuJoCo). * Section 3.3 is environment specific, so it should be moved to Section 4.
4. Reproducibility *

Are the results of this submission easily reproducible? (Please refer to our reproducibility guidelines https://ijcai.org/reproducibility/).
Convincing
Credible
Irreproducible
5. Reproducibility Details

If your answer to the previous question is different from "Convincing", please provide a brief justification.
Answer: There is no source code, and some aspects of the training and architecture are not clear.
6. Ethical Concerns *

Independent of your judgement of the quality of the work, are there any ethical concerns with regard to responsible research or potential negative societal impacts of this submission that must be considered by IJCAI before the paper can be accepted? Papers
with a yes here will undergo additional ethical screening by senior members of the program committee and the Ethics Chair.
Answer: No
7. Ethical Concerns Details

If your answer to the previous question is "Yes", please provide a brief justification.
Answer: Not responded
8. Score Justification. *

Justify your score in a few lines.
Answer: The paper considers an important and interesting problem, and the proposed method seems to be innovative. However, the paper includes some hidden assumptions (communication), and its presentation lacks clarity.
PC #2
PC form

1. Summary *

Please briefly summarize the main claims/contributions of the submission in your own words. (Please do not include your evaluation of the paper here).
Answer: This paper proposes Safe Dreamers, a model-based safe multi-agent reinforcement learning framework that integrates multi-agent world models with Lagrangian safety constraints to enable proactive safety learning via latent space imagination, aiming to address the trade-off between sample efficiency and safety guarantees in MARL for safety-critical applications. The framework is evaluated on the SMAC benchmark with casualty aversion constraints, showing 25× higher sample efficiency than the state-of-the-art model-free baseline MACPO and successful satisfaction of strict safety constraints where reactive methods fail. The methodology formulates the problem as a C-Dec-POMDP, designs a cost-aware world model for joint reward and cost prediction, and adopts an adaptive Lagrangian multiplier to balance task performance and safety, with a centralized training and decentralized execution paradigm for multi-agent coordination.
2. Strengths *

What are the main strengths of the submission? Please focus on novelty (how novel are the concepts, problems addressed, or methods introduced in the submission), soundness (is the submission technically sound), clarity (is the submission well-organized and
clearly written), and significance (comment on the likely impact the submission may have on the AI research community as a whole or on its own sub-field).
Answer: The work makes a novel contribution by being the first to unify multi-agent world models with Lagrangian safety constraints, filling the critical gap between model-based MARL’s sample efficiency and constrained policy optimization’s safety guarantees. The proposed cost-aware world model enables proactive safety learning in imagination, eliminating the need for real-world safety violations and thus being well-suited for safety-critical domains—a key advancement over reactive safe MARL methods.
3. Weaknesses *

What are the weaknesses of the submission? Please focus on novelty, soundness, clarity, and significance.
Answer: The paper is limited to cooperative multi-agent scenarios only, with no exploration of competitive or mixed-motive settings, which severely restricts the generalizability of the Safe Dreamers framework and its applicability to real-world multi-agent systems that often involve non-cooperative interactions. The cost prediction accuracy is heavily reliant on latent space representation tuning, yet the paper provides minimal details on the tuning process, hyperparameter sensitivity, and how to optimize latent space encoding for safety-relevant dynamics, leading to poor reproducibility and practical implementation challenges. The theoretical foundation is notably weak—there are no formal proofs for constraint satisfaction in the imagined latent space, nor analysis of the convergence properties of the adaptive Lagrangian multiplier and the overall policy optimization process, which is a critical shortcoming for a framework claiming strict safety guarantees. The computational tradeoff analysis is superficial, with only a rough wall-clock time comparison and no detailed evaluation of the per-step computation overhead of the world model, making it impossible to assess the framework’s scalability for larger and more complex multi-agent environments beyond SMAC’s limited agent counts. The safety constraint is narrowly defined as casualty aversion in SMAC; there is no evaluation on other typical safety constraints (e.g., collision avoidance, resource limits), raising doubts about the framework’s ability to generalize to different safety-critical domains. Additionally, the paper has minor technical errors in the mathematical formulation of the RSSM components, which undermines the technical rigor of the methodology section.
