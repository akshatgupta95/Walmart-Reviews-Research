from collections import defaultdict
import string
import pickle
import re

class Indexer:

	def __init__(self, docs=None):
		self.docs = docs

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

	def _get_docs_simple_query(self, search_query):
	    with open('inv_idx.pickle', 'rb') as f:
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

	def _get_docs_phrase_query(self, search_query):
	    with open('inv_idx.pickle', 'rb') as f:
	    	inv_idx = pickle.load(f)
	    query_terms = [
	        re.sub(r'[^\w\s]','',q).lower()
	        for q in search_query.split(' ')
	    ]
	    
	    docs_to_pos = defaultdict(list)
	    for q_term in query_terms:
	        docs_to_pos_q_term = inv_idx[q_term]
	        for doc_id in docs_to_pos_q_term.keys():
	            if doc_id in docs_to_pos.keys():
	                docs_to_pos[doc_id].append(docs_to_pos_q_term[doc_id])
	            else:
	                docs_to_pos[doc_id] = [docs_to_pos_q_term[doc_id]]

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

	def index_documents(self):
		inv_idx = self.create_inverted_index()
		with open('inv_idx.pickle', 'wb') as f:
			pickle.dump(inv_idx, f)

	def get_docs(self, search_query, search_type='simple_query'):
		if search_type=='simple_query' or len(search_query.split(' ')) < 2:
			return self._get_docs_simple_query(search_query)
		else:
			return self._get_docs_phrase_query(search_query)