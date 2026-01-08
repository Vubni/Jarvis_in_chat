import re
import math
from functions.functions import My_message
from TelegramClient import Jarvis_client
from create_bot import bot
from config import jarvis_all, data_users
from modules.calculator.settings import PATH

status = True

class Calculator:
    def __init__(self):
        self.functions = {
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x)),
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log
        }
        self.constants = {
            'pi': math.pi,
            'e': math.e
        }
        self.operators = {
            '+': (1, lambda a, b: a + b),
            '-': (1, lambda a, b: a - b),
            '*': (2, lambda a, b: a * b),
            '/': (2, lambda a, b: a / b),
            '**': (3, lambda a, b: a ** b),
            '%': (4, lambda a, b: a % b)
        }

    def parse_expression(self, expr):
        expr = expr.replace(',', '.').replace(' ', '').replace('^', '**')
        tokens = self.tokenize(expr)
        postfix = self.shunting_yard(tokens)
        return self.evaluate_postfix(postfix)

    def tokenize(self, expr):
        token_pattern = re.compile(r"""
            (\d+\.\d+|\d+|              # Числа
            [+\-*/%^()]|                # Операторы и скобки
            \*\*|                       # Степень
            \b(sin|cos|tan|sqrt|log|ln)\b|  # Функции
            \b(pi|e)\b)                 # Константы
        """, re.VERBOSE)
        
        tokens = []
        i = 0
        while i < len(expr):
            if expr[i] == ' ':
                i += 1
                continue
                
            if expr[i] in '()':
                tokens.append(('PAREN', expr[i]))
                i += 1
                continue
            
            match = token_pattern.match(expr, i)
            if match:
                token = match.group()
                if token in self.functions:
                    tokens.append(('FUNC', token))
                elif token in self.constants:
                    tokens.append(('CONST', token))
                elif token in self.operators:
                    tokens.append(('OP', token))
                elif token.replace('.', '').isdigit() or token == '.':
                    tokens.append(('NUM', float(token) if '.' in token else int(token)))
                i += len(token)
            else:
                raise ValueError(f"Неизвестный символ: {expr[i]}")
        return tokens

    def shunting_yard(self, tokens):
        output = []
        stack = []
        for token in tokens:
            type_, value = token
            if type_ in ('NUM', 'CONST'):
                output.append(token)
            elif type_ == 'FUNC':
                stack.append((type_, value))
            elif type_ == 'OP':
                precedence, _ = self.operators[value]
                while stack:
                    stack_top_type, stack_top_val = stack[-1]
                    if stack_top_type != 'OP':
                        break
                    stack_precedence, _ = self.operators[stack_top_val]
                    if precedence <= stack_precedence:
                        output.append(stack.pop())
                    else:
                        break
                stack.append((type_, value))
            elif value == '(':
                stack.append(('PAREN', '('))
            elif value == ')':
                while stack and stack[-1][1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1][1] == '(':
                    stack.pop()
        while stack:
            output.append(stack.pop())
        return output

    def evaluate_postfix(self, postfix):
        stack = []
        for token in postfix:
            type_, value = token
            if type_ == 'NUM':
                stack.append(value)
            elif type_ == 'CONST':
                stack.append(self.constants[value])
            elif type_ == 'FUNC':
                arg = stack.pop()
                stack.append(self.functions[value](arg))
            elif type_ == 'OP':
                b = stack.pop()
                a = stack.pop()
                stack.append(self.operators[value][1](a, b))
        return stack[0]

    def format_result(self, value):
        if isinstance(value, int) or value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else str(int(value))

async def extract_math_expression(text):
    # Регулярное выражение для поиска выражений с '=' в конце
    pattern = r'(\b[\d+\-*/%^().\s]+?=\s*(?=\s*\n|\s*$|\s+[^\d\s]))'
    matches = re.findall(pattern, text, re.MULTILINE)
    return [m.rstrip('= \t').strip() for m in matches] if matches else None

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return

    message = new_message.message
    text = message.text

    if len(text) >= 80 or any(kw in text.lower() for kw in ["минут", "секунд", "часов", "дня", "дней", "через"]):
        return

    calculator = Calculator()
    expressions = await extract_math_expression(text)
    
    if not expressions:
        return False

    new_text = []
    for line in text.split('\n'):
        modified_line = line
        for expr in expressions:
            # Экранируем спецсимволы для корректного поиска
            escaped_expr = re.escape(f"{expr}=")
            # Ищем выражение с '=' в конце
            pattern = rf'(?<!\S){escaped_expr}(?=\s*(?:\n|$|[^\d]))'
            replacement = f"{expr} = {calculator.format_result(calculator.parse_expression(expr))}"
            modified_line = re.sub(pattern, replacement, modified_line, count=1)
        new_text.append(modified_line)
    new_text = '\n'.join(new_text)

    try:
        user_id = message.from_id.user_id if hasattr(message.from_id, 'user_id') else message.from_id
        if jarvis.user.id == user_id:
            await jarvis.client.edit_message(message.chat_id, message.id, new_text)
            await bot.send_message(jarvis.user.id, 
                f"Я отредактировал сообщение в чате <b>'<a href='tg://user?id={new_message.chat.id}'>{new_message.chat.first_name}</a>'</b>, решив пример", 
                parse_mode='HTML', disable_notification=True)
    except Exception as e:
        print(f"Ошибка обновления сообщения: {e}")
    return False