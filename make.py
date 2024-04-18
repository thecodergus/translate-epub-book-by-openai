import argparse
import time
import openai
import ast
from bs4 import BeautifulSoup as bs
from ebooklib import epub
from rich import print

# Classe que representa o ChatGPT e sua função de tradução
class ChatGPT:
    def __init__(self, key):
        self.key = key

    def translate(self, text):
        print(text)
        openai.api_key = self.key
        try:
            # Chamada à API do OpenAI para tradução
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        # Prompt em inglês para economizar tokens
                        "content": f"Please help me to translate `{text}` to Brazilian Portuguese, please return only translated content not include the origin text, maintain the same formatting as the original textual list individual elements ",
                    }
                ],
            )
            # Extrair o texto traduzido do resultado da API
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
            t_text = t_text.strip("\n")
            try:
                t_text = ast.literal_eval(t_text)
            except Exception:
                pass
            time.sleep(3)
        except Exception as e:
            print(str(e), "will sleep 60 seconds")
            time.sleep(60)
            # Tentativa novamente da chamada à API do OpenAI para tradução
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                         "content": f"Please help me to translate `{text}` to Brazilian Portuguese, please return only translated content not include the origin text, maintain the same formatting as the original textual list individual elements",
                    }
                ],
            )
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
            t_text = t_text.strip("\n")
            try:
                t_text = ast.literal_eval(t_text)
            except Exception:
                pass
        print(t_text)
        return t_text

# Classe que representa o livro EPUB e sua função de tradução
class BEPUB:
    def __init__(self, epub_name, key, batch_size):
        self.epub_name = epub_name
        self.translate_model = ChatGPT(key)
        self.origin_book = epub.read_epub(self.epub_name)
        self.batch_size = batch_size

    def translate_book(self):
        new_book = epub.EpubBook()
        new_book.metadata = self.origin_book.metadata
        new_book.spine = self.origin_book.spine
        new_book.toc = self.origin_book.toc
        batch_p = []
        batch_count = 0
        for i in self.origin_book.get_items():
            if i.get_type() == 9:
                soup = bs(i.content, "html.parser")
                p_list = soup.findAll("p")
                for p in p_list:
                    if p.text and not p.text.isdigit():
                        batch_p.append(p)
                        batch_count += 1
                        if batch_count == self.batch_size:
                            translated_batch = self.translate_model.translate([p.text for p in batch_p])
                            batch_p[-1].string = batch_p[-1].text + ' '.join(map(str, translated_batch))
                            batch_p = []
                            batch_count = 0
                if batch_p:
                    translated_batch = self.translate_model.translate([p.text for p in batch_p])
                    for j, c_p in enumerate(batch_p):
                        c_p.string = c_p.text + translated_batch[j]
                    batch_p = []
                    batch_count = 0
                i.content = soup.prettify().encode()
            new_book.add_item(i)
        name = self.epub_name.split(".")[0]
        epub.write_epub(f"{name}_translated.epub", new_book, {})

# Verificação se o script está sendo executado diretamente
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--book_name",
        dest="book_name",
        type=str,
        help="your epub book name",
    )
    parser.add_argument(
        "--openai_key",
        dest="openai_key",
        type=str,
        default="",
        help="openai api key",
    )
    parser.add_argument(
        "--batch_size",
        dest="batch_size",
        type=int,
        default=2,
        choices=[2,3,4,5],
        help="the batch size paragraph for translation , max is 5",
    )
    options = parser.parse_args()
    OPENAI_API_KEY = options.openai_key
    if not OPENAI_API_KEY:
        raise Exception("Need openai API key, please google how to")
    if not options.book_name.endswith(".epub"):
        raise Exception("please use epub file")
    e = BEPUB(options.book_name, OPENAI_API_KEY, options.batch_size)
    e.translate_book()
