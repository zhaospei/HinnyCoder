from transformers import AutoTokenizer, AutoModelForCausalLM
import torch 
from awq import AutoAWQForCausalLM

BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"

def deepseek_build_masked_func(masked_func: str):
    masked_func = masked_func.replace('<FILL_FUNCTION_BODY>', FILL_TOKEN)
    return BEGIN_TOKEN + masked_func + END_TOKEN

instruction = """class CodeCacheEventWalker extends AbstractCompilationWalker { 
    private CodeCacheWalkerResult result = new CodeCacheWalkerResult(); 
    private static final Logger logger = LoggerFactory.getLogger(CodeCacheEventWalker.class); 
    public CodeCacheEventWalker(IReadOnlyJITDataModel model) { 
        super(model); 
    } 
    
    @Override
    public void reset() {
        result.reset(); 
    } 
    
    @Override
    public void visit(IMetaMember metaMember) {
        <FILL_FUNCTION_BODY>
    } 
    
    public CodeCacheWalkerResult getResult() { 
        return result; 
    } 
}
""" 

input = deepseek_build_masked_func(instruction)


model_id = "TheBloke/deepseek-coder-1.3b-base-AWQ"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
tokenizer.padding_side = "left"


model = AutoAWQForCausalLM.from_quantized(model_id, fuse_layers=True,
                                          trust_remote_code=False, safetensors=True)

model.eval()

model_input = tokenizer(input, return_tensors="pt").to("cuda")

output = ''

with torch.no_grad():
    output = tokenizer.decode(model.generate(**model_input, max_new_tokens=400, pad_token_id=tokenizer.eos_token_id)[0], skip_special_tokens=True)

print(output)