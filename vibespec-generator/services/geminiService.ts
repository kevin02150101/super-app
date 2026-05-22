
import { GoogleGenAI } from "@google/genai";
import { TechSpec } from "../types";

const API_KEY = (process.env.API_KEY || process.env.GEMINI_API_KEY || "").trim();
export const HAS_API_KEY = Boolean(API_KEY);

// Always initialize GoogleGenAI with a named apiKey parameter.
const ai = new GoogleGenAI({ apiKey: API_KEY });

function refineErrorMessage(error: unknown): string {
  if (!API_KEY) {
    return "Gemini API key is missing. Set GEMINI_API_KEY in Vercel project settings, then redeploy.";
  }
  const text = String((error as any)?.message || error || "");
  if (/401|403|unauthorized|forbidden/i.test(text)) {
    return "Gemini request was rejected (auth/permission). Check your API key and allowed referrers.";
  }
  if (/429|quota|rate/i.test(text)) {
    return "Gemini quota/rate limit reached. Wait a moment or use a key with available quota.";
  }
  if (text) {
    return `AI refinement failed: ${text}`;
  }
  return "An error occurred during AI refinement.";
}

export const assistField = async (fieldName: string, currentValue: string, context: string): Promise<string> => {
  if (!API_KEY) {
    throw new Error("Gemini API key is missing. Set GEMINI_API_KEY in Vercel project settings, then redeploy.");
  }

  // Use systemInstruction for setting the model's persona and output constraints
  const systemInstruction = `You are an experienced product manager and technical advisor.
The user is currently filling out a technical specification document.

Requirements:
- Respond in English.
- Be concrete and actionable; the audience is software engineers.
- Keep the total length under 80 words.
- Reply with the generated content only \u2014 no extra explanations, labels, or preamble.`;

  const prompt = `The user is filling out the "${fieldName}" field of a technical specification.

    Known project context: ${context}
    Current value: ${currentValue || "(empty)"}

    Based on the context, please:
    1. If the value is empty, draft a professional, concrete description.
    2. If a value already exists, refine it for greater technical depth and tighter logic.`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        systemInstruction,
      },
    });
    // Access the generated text using the .text property (not a method)
    return response.text?.trim() || "";
  } catch (error) {
    console.error("AI Assist Error:", error);
    throw new Error(refineErrorMessage(error));
  }
};

export const refineSpecWithAI = async (spec: TechSpec): Promise<string> => {
  // Use systemInstruction for the complex persona required for this task
  const systemInstruction = `You are a world-class senior software architect and Vibe Coding expert.
The user's goal is to generate a high-quality Technical Specification that AI coding assistants (such as Cursor, Windsurf, or Replit) can execute on precisely.`;

  const prompt = `Please expand and refine the following input data:
    ${JSON.stringify(spec, null, 2)}

    The output document must be written in English and include the following structure:
    1. **Project Vision & Core Value**: a refined description of the project goals.
    2. **Functional Requirements**: expand the user-provided modules into concrete logic and behavior descriptions.
    3. **UI Specification**: detailed layout, color system, and responsive behavior.
    4. **Tech Stack & Implementation Strategy**: concrete implementation guidance for ${spec.techStack.frontend} and ${spec.techStack.api}.
    5. **Data Schema**: a structured table schema.
    6. **Vibe Coding Prompt Sequence**: 3-5 concrete prompts.

    Output format: pure Markdown.
    Style: professional, clearly structured, and highly friendly to AI coding assistants.`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: prompt,
      config: {
        systemInstruction,
        // Using thinking budget for complex technical reasoning
        thinkingConfig: { thinkingBudget: 4000 }
      }
    });

    // Directly access .text property from the response
    return response.text || "Generation failed. Please try again later.";
  } catch (error) {
    console.error("Gemini Error:", error);
    return refineErrorMessage(error);
  }
};
