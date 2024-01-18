from transformers import AutoModelForCausalLM, CodeLlamaTokenizer
import torch

model_base = 'codellama/CodeLlama-7b-hf'

tokenizer = CodeLlamaTokenizer.from_pretrained(model_base)

tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(model_base, load_in_8bit=True, device_map='auto', torch_dtype=torch.float16)

model.eval()

text = '''contract BasicToken is ERC20Basic { using SafeMath for uint256; mapping(address => uint256) balances; uint256 totalSupply_; /** * @dev Total number of tokens in existence */ function totalSupply() public view returns (uint256) { return totalSupply_; } /** * @dev Transfer token for a specified address * @param _to The address to transfer to. * @param _value The amount to be transferred. */ function transfer(address _to, uint256 _value) public returns (bool) { require(_value <= balances[msg.sender]); require(_to != address(0)); balances[msg.sender] = balances[msg.sender].sub(_value); balances[_to] = balances[_to].add(_value); emit Transfer(msg.sender, _to, _value); return true; } /** * @dev Gets the balance of the specified address. * @param _owner The address to query the the balance of. * @return An uint256 representing the amount owned by the passed address. */ function balanceOf(address _owner) public view returns (uint256) {<FILL_ME>} }'''

model_input = tokenizer(text, return_tensors="pt", padding=True, max_length=2048, truncation=True).to("cuda")

with torch.no_grad():
    output = tokenizer.decode(model.generate(**model_input, max_new_tokens=1028, pad_token_id=tokenizer.eos_token_id)[0], skip_special_tokens=True)

print(output)