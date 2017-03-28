from collections import defaultdict
from collections import Counter
from sklearn.metrics import mutual_info_score
from nltk.corpus import stopwords
import numpy as np
import operator
import re

stop = set(stopwords.words('english'))

class MutualInformation:

	def __init__(self, txt_data=None, search_query=None):
		self.txt_data = txt_data
		self.info_pairs = self._process_txt()
		self.search_query = search_query
		self.summary = self._get_search_query_summary()

	def _process_txt(self):
		vocab = set()
		doc_term = defaultdict(dict)
		for txt in self.txt_data:
			terms = [re.sub(r'[^\w\s]','',s).lower() for s in txt.split(' ')]
			vocab = vocab.union(terms)
			
		for word in vocab:
			for doc_id in range(len(self.txt_data)):
				if doc_id not in doc_term.keys():
					doc_term[doc_id] = defaultdict(int)
				doc_term[doc_id][word] = 0

		for word in vocab:
			for doc_id, txt in enumerate(self.txt_data):
				terms = [re.sub(r'[^\w\s]','',s).lower() for s in txt.split(' ')]
				if word in terms:
					doc_term[doc_id][word] = 1

		return self._get_info_pairs(
			doc_term=doc_term,
			vocab=vocab
		)

	def _get_info_pairs(self, doc_term=None, vocab=None):
		N = len(doc_term.keys())

		info_pairs = defaultdict(dict)
		for w1 in vocab:
			for w2 in vocab:
				p_X_w1_1 = 0
				p_X_w2_1 = 0
				p_X_w1_1_w2_1 = 0
				for doc_id in doc_term.keys():
					w1_present = False
					w2_present = False
					if doc_term[doc_id][w1] > 0:
						w1_present = True
						p_X_w1_1 += 1
					if doc_term[doc_id][w2] > 0:
						w2_present = True
						p_X_w2_1 += 1
					if w1_present and w2_present:
						p_X_w1_1_w2_1 += 1

				# P(X_w1 = 1)
				p_X_w1_1 = (p_X_w1_1 + 0.5) / (float(N) + 1)

				# P(X_w2 = 1)
				p_X_w2_1 = (p_X_w2_1 + 0.5) / (float(N) + 1)

				# P(X_w1=1, X_w2=1)
				p_X_w1_1_w2_1 = (p_X_w1_1_w2_1 + 0.25) / (float(N) + 1)

				# P(X_w1 = 0) = 1 - P(X_w1 = 1)
				p_X_w1_0 = 1. - p_X_w1_1

				# P(X_w2 = 0) = 1 - P(X_w2 = 1)
				p_X_w2_0 = 1. - p_X_w2_1

				# P(X_w1=1, X_w2=0) + P(X_w1=1, X_w2=1) = P(X_w1=1)
				p_X_w1_1_w2_0 = p_X_w1_1 - p_X_w1_1_w2_1

				# P(X_w1=0, X_w2=1) + P(X_w1=1, X_w2=1) = P(X_w2=1)
				p_X_w1_0_w2_1 = p_X_w2_1 - p_X_w1_1_w2_1

				# P(X_w1=0, X_w2=0) + P(X_w1=0, X_w2=1) = P(X_w1=0)
				p_X_w1_0_w2_0 = p_X_w1_0 - p_X_w1_0_w2_1

				I_w1_w2 = (p_X_w1_1_w2_1 * np.log2(p_X_w1_1_w2_1 / (p_X_w1_1 * p_X_w2_1))) +\
						(p_X_w1_0_w2_0 * np.log2(p_X_w1_0_w2_0 / (p_X_w1_0 * p_X_w2_0))) +\
						(p_X_w1_1_w2_0 * np.log2(p_X_w1_1_w2_0 / (p_X_w1_1 * p_X_w2_0))) +\
						(p_X_w1_0_w2_1 * np.log2(p_X_w1_0_w2_1 / (p_X_w1_0 * p_X_w2_1)))

				info_pairs[w1][w2] = I_w1_w2

		return info_pairs


	def _get_search_query_summary(self):
		search_terms = self.search_query.split(' ')
		all_info = defaultdict(int)
		for s_t in search_terms:
			if s_t not in self.info_pairs.keys():
				continue
			sorted_mut_infos = sorted(self.info_pairs[s_t].items(), key=lambda x:x[1], reverse=True)[:10]
			mut_assoc_words = [c[0] for c in sorted_mut_infos]
			for word in mut_assoc_words:
				all_info[word] += 1
		info = [c[0] for c in sorted(all_info.items(), key=lambda x:x[1], reverse=True)[:10]]

		return self._get_summary(info)


	def _get_summary(self, info):
		word_counts = defaultdict(int)
		for word in info:
			count = 0
			for txt in self.txt_data:
				terms = [re.sub(r'[^\w\s]','',s).lower() for s in txt.split(' ')]
				for term in terms:
					if term == word:
						word_counts[word] += 1
		summary_words_counts = sorted(word_counts.items(), key=operator.itemgetter(1), reverse=True)
		for summary_word_count in summary_words_counts:
			word = summary_word_count[0]
			if word in stop:
				summary_words_counts.remove(summary_word_count)

		return ' '.join([s[0].strip() for s in summary_words_counts])