from src.scraper import WikipediaScraper



scraper = WikipediaScraper()
scraper.get_final_dict()
scraper.to_json_file('leaders_data.json')