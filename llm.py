
from langchain.memory import  ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.llms import HuggingFacePipeline
from auto_gptq import AutoGPTQForCausalLM
from transformers import (
    AutoTokenizer,
    pipeline,
    logging,
    TextIteratorStreamer,
    T5ForConditionalGeneration
)


model_name_or_path = "TheBloke/WizardLM-13B-V1.2-GPTQ"

use_triton = False

tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)

logging.set_verbosity(logging.CRITICAL)
# quantizing model for resource-constrained environments
model = AutoGPTQForCausalLM.from_quantized(model_name_or_path,
                                          #  model_basename=model_basename,
                                           use_safetensors=True,
                                           trust_remote_code=True,
                                           device="cuda:0",
                                           use_triton=use_triton,
                                           quantize_config=None)



streamer = TextIteratorStreamer(tokenizer, skip_prompt=True)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=2048,
    temperature=0.6,
    pad_token_id=tokenizer.eos_token_id,
    top_p=0.95,
    repetition_penalty=1.2,
    streamer=streamer
)


llm = HuggingFacePipeline(pipeline=pipe)

memory = ConversationBufferWindowMemory()


title_model= T5ForConditionalGeneration.from_pretrained("czearing/article-title-generator")
title_tokenizer = AutoTokenizer.from_pretrained("czearing/article-title-generator")



def generate_title(input_text):
    input_ids = title_tokenizer(input_text, return_tensors="pt").input_ids
    outputs_token = title_model.generate(input_ids)
    output= title_tokenizer.decode(outputs_token[0], skip_special_tokens=True)
    return output
