# AI Enhanced Translator

The **AI Enhanced Translator** is a powerful tool that harnesses the capabilities of artificial intelligence to provide advanced translation services. This tool is designed to streamline and enhance the translation process by leveraging the OpenAI GPT-3.5 Turbo model.

[Screenshot](img/photo_2023-09-28_19-38-07.jpg) of translation from very informal Russian to English.

**Table of Contents**
- [AI Enhanced Translator](#ai-enhanced-translator)
  - [Key Features](#key-features)
  - [Quick Start](#quick-start)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [Some prompt engineering takeaways](#some-prompt-engineering-takeaways)

## Key Features

- **High-Quality Translation**: The AI Enhanced Translator offers top-notch translations that excel in handling informal language, humor, jargon, and complex text.
- **Multilingual Support**: It supports a wide range of languages, making it a versatile tool for various translation needs.
- **Adaptive Writing Styles**: The translator adapts to different writing styles, ensuring that the translated text maintains the intended tone and context.
- **Cultural Nuance Consideration**: It takes cultural nuances into account, resulting in translations that are culturally sensitive and accurate.

## Quick Start

To use the AI Enhanced Translator:

1. Ensure you have Python 3.x installed (tested on 3.9 and 3.10).
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Obtain an OpenAI API key by [signing up](https://platform.openai.com/) and creating personal API key.
4. Set your API key:
   - As an environment variable named `OPENAI_API_KEY`.
   - In the `.env.local` file.
   - In the UI by clicking the `Switch API Key` button.

## Usage

1. Input your text into the provided text field.
2. Quick translation using Google Translate will be periodically updated as you type.
3. For a more refined translation using the AI model, press `Ctrl+Enter`.

Please note that the AI-powered translation may take a bit longer but offers significantly improved quality.

## Contributing

We welcome contributions to the AI Enhanced Translator project. If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear and descriptive messages.
4. Push your changes to your fork.
5. Submit a pull request to the main repository.

Your contributions will help make this tool even more valuable for users worldwide. Thank you for your support!

## Some prompt engineering takeaways

Here are the main lessons I've learned from my first experience with the API ChatGPT. I aimed to keep things simple and straightforward, and here's what I discovered:

1. **One Prompt, One Task:** When using ChatGPT, it's best to stick to one task per prompt. While it may be tempting to create branching prompt with different outcomes, this approach can lead to instability in the responses. It's generally more reliable to keep each prompt focused on a single task or question.
2. **Custom Response Format:** While many recommend enforcing ChatGPT responses in JSON format, I found this approach to be somewhat cumbersome. Instead, I developed my own response format that takes into account the nuances of how the language model works. Simplicity and clarity in the response format can make working with ChatGPT more straightforward.
3. **Flags:** To gauge the complexity of responses, I moved away from using a simple rating scale and instead began detecting elements like sarcasm, humor, or complex topics. The model responds with "Yes" or "No" to indicate the presence of these elements, and I count the number of "Yes" answers to determine if a more complex reply is needed. This approach proved to be both simple and stable. In general, it's best to **keep as much of the logic as possible on the client side, rather than relying on the LLM response**. See [this template](https://github.com/GreenWizard2015/AIEnhancedTranslator/blob/fd7bdd567100f09050ac13431032e682db0a92be/data/translate_shallow.txt) for more details.
4. **Explicit Requests:** Sometimes, it's not enough to ask for something in a general way, like "issues with ...: {list}". To get more precise responses, it can be helpful to request a list, specify the minimum number of elements, and explicitly begin the list while describing the meaning of its elements. Providing clear context in your prompts can lead to more accurate and relevant responses. See [this template](https://github.com/GreenWizard2015/AIEnhancedTranslator/blob/fd7bdd567100f09050ac13431032e682db0a92be/data/translate_deep.txt#L8-L9) for more details.
5. **Translation of the notifications:** It's interesting that you can request a translation of some messages for UI directly in the prompt. This is extremely unusual for me as a programmer. See [this template](https://github.com/GreenWizard2015/AIEnhancedTranslator/blob/e1c0975202e926e339ee10766810f26d710a2f4a/prompts/translate_shallow.txt#L14) for more details. Ultimately, I chose not to pursue this approach, because it's reducing the stability of the system. But it's a really interesting idea, in my opinion.
6. **Prompt optimization:** After receiving the first results, I started optimizing the size and stability of the prompts. AI doesn't care about grammar and spelling, so we can shorten the prompt to the minimum necessary for stable text generation. This improves the stability of the output and reduces the cost of requests. However, I haven't shortened the critically important parts of the prompt. By the way, basic optimization can be done quite well with ChatGPT. I assume that the process of refining prompts can be automated without significant costs.
