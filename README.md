# Wikipedia Scraper
[![forthebadge made-with-python](https://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)


## 🏢 Description

 In this project I create a scraper that builds a JSON file with the political leaders of each country I get from [this API](https://country-leaders.onrender.com/docs).
 Include in this file the first paragraph of the Wikipedia page of these leaders. 
 Also, I used the asyncio module for asynchronous link processing, as well as BeautifulSoup for scraping data from HTML pages and regular expressions for data cleaning.









![wiki_logo](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Wikipedia-Logo-black-and-white.jpg/480px-Wikipedia-Logo-black-and-white.jpg)

## 📦 Repo structure

```
.
├── src/
│   ├── scraper.py
├── .gitignore
├── main.py
├── leaders_data.json
└── README.md
```

## 🛎️ Usage
1. Clone the repository to your local machine.



2 .To run the script, you can execute the `main.py` file from your command line:

    ```
    python main.py
    ```

3. The script creates an instance of the WikipediaScraper class and builds a dictionary with the country code as a key and the first paragraph of the Wikipedia bio for each leader of a specific country as a value.
   The resulting dictionary is saved to a "leaders_data.json" file in your root directory.

```python
scraper = WikipediaScraper()
scraper.get_final_dict()
scraper.to_json_file('leaders_data.json')
```
## ⏱️ Timeline

This project took two days for completion.

## 📌 Personal Situation
This project was done as part of the AI Boocamp at BeCode.org. 

Connect with me on [LinkedIn](www.linkedin.com/in/ihor-afanasiev-a50798268).
