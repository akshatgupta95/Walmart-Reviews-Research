from collections import defaultdict
import itertools
import string
import pickle
import re

class Indexer:

	def __init__(self, docs=None, item_id=None):
		self.docs = docs
		self.item_id = item_id

	def create_term_to_pos_for_doc(self, doc_id):
		term_to_pos = {}
		terms = [re.sub(r'[^\w\s]','',s).lower() for s in self.docs[doc_id].split(' ')]
		for idx, term in enumerate(terms):
	 		if term in term_to_pos:
				term_to_pos[term].append(idx)
			else:
				term_to_pos[term] = [idx]
		return term_to_pos

	def create_forward_index(self):
		forward_index = {}
		for doc_id in range(len(self.docs)):
			forward_index[doc_id] = self.create_term_to_pos_for_doc(doc_id)
		return forward_index

	def create_inverted_index(self):
		fwd_index = self.create_forward_index()
		inverted_index = defaultdict(dict)
		for doc_id in fwd_index.keys():
			terms_to_pos = fwd_index[doc_id]
			for term in terms_to_pos.keys():
				pos = terms_to_pos[term]
				if term in inverted_index.keys():
					if doc_id in inverted_index[term]:  
						inverted_index[term][doc_id].extend(pos)
					else:
						inverted_index[term][doc_id] = pos
				else:
					inverted_index[term] = {doc_id : pos}
		return inverted_index

	def _get_docs_simple_query(self, search_query, item_id):
		file_name = 'inv_idx%s.pickle' % item_id
		with open(file_name, 'rb') as f:
			inv_idx = pickle.load(f)

		query_terms = [
			re.sub(r'[^\w\s]','',q).lower()
			for q in search_query.split(' ')
		]
		retrieved_docs = []
		for q_term in query_terms:
			retrieved_docs.extend(
				inv_idx[q_term].keys()
			)
		return list(set(retrieved_docs))

	def _get_docs_phrase_query(self, search_query, item_id):
		file_name = 'inv_idx%s.pickle' % item_id
		with open(file_name, 'rb') as f:
			inv_idx = pickle.load(f)
		query_terms = [
			re.sub(r'[^\w\s]','',q).lower()
			for q in search_query.split(' ')
		]
	    
		docs_to_pos = defaultdict(list)
		for q_term in query_terms:
			docs_to_pos_q_term = inv_idx[q_term]
			if len(docs_to_pos_q_term) == 0:
				return []
			for doc_id in docs_to_pos_q_term.keys():
				if doc_id in docs_to_pos.keys():
					docs_to_pos[doc_id].append(docs_to_pos_q_term[doc_id])
				else:
					docs_to_pos[doc_id] = [docs_to_pos_q_term[doc_id]]

		for k in docs_to_pos.keys():
			if len(docs_to_pos[k]) < len(query_terms):
				docs_to_pos.pop(k, None)

		for doc_id in docs_to_pos.keys():
			pos = docs_to_pos[doc_id]
			for idx, pos_list in enumerate(pos):
				for i in range(len(pos_list)):
					pos_list[i] -= idx
	    
		retrieved_docs = []
	    
		for doc_id in docs_to_pos.keys():
			pos_list = docs_to_pos[doc_id]
			if len(pos_list) >= 2:
				intersection = set(pos_list[0])
				for p in pos_list[1:]:
					intersection = intersection & set(p)
				if len(intersection) >= 1:
					retrieved_docs.append(doc_id)
	                
		return retrieved_docs

	def _get_docs_phrase_query_word_range(self, search_query, item_id, word_range=1):
		file_name = 'inv_idx%s.pickle' % item_id
		with open(file_name, 'rb') as f:
			inv_idx = pickle.load(f)
		query_terms = [
			re.sub(r'[^\w\s]','',q).lower()
			for q in search_query.split(' ')
		]
	    
		docs_to_pos = defaultdict(list)
		for q_term in query_terms:
			docs_to_pos_q_term = inv_idx[q_term]
			if len(docs_to_pos_q_term) == 0:
				return []
			for doc_id in docs_to_pos_q_term.keys():
				if doc_id in docs_to_pos.keys():
					docs_to_pos[doc_id].append(docs_to_pos_q_term[doc_id])
				else:
					docs_to_pos[doc_id] = [docs_to_pos_q_term[doc_id]]

		for k in docs_to_pos.keys():
			if len(docs_to_pos[k]) < len(query_terms):
				docs_to_pos.pop(k, None)
	    
		retrieved_docs = []

		for doc_id in docs_to_pos.keys():
			pos_list = docs_to_pos[doc_id]
			idx_pos_tuples = []
			for idx, curr_pos_list in enumerate(pos_list):
				for p in curr_pos_list:
					idx_pos_tuples.append((p, idx))
			idx_pos_tuples = sorted(idx_pos_tuples, key=lambda x: x[0])
			window_size = len(search_query.split(' '))
			pos_combs = itertools.combinations(idx_pos_tuples, window_size)
			for comb in pos_combs:
				y_values = set([c[1] for c in comb])
				if len(y_values) != window_size:
					continue
				else:
					x_values = [c[0] for c in comb]
					if max(x_values) - min(x_values) <= word_range:
						retrieved_docs.append(doc_id)
						break
	                
		return retrieved_docs

	def index_documents(self):
		inv_idx = self.create_inverted_index()
		file_name = 'inv_idx%s.pickle' % self.item_id
		with open(file_name, 'wb') as f:
			pickle.dump(inv_idx, f)

	def get_docs(self, search_query, search_type='phrase_query', item_id=None):
		if search_type=='simple_query' or len(search_query.split(' ')) < 2:
			return self._get_docs_simple_query(search_query, item_id)
		else:
			return self._get_docs_phrase_query_word_range(search_query, item_id, word_range=5)