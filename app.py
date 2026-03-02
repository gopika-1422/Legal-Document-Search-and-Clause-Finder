from flask import Flask, render_template, request, jsonify
import os
import json
import math
import re
from collections import defaultdict, Counter
from datetime import datetime
import PyPDF2
from docx import Document as DocxDocument

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['INDEX_FILE'] = 'inverted_index.json'
app.config['METADATA_FILE'] = 'documents_metadata.json'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class LegalDocumentSearchEngine:
    def __init__(self):
        self.inverted_index = {}
        self.documents = {}
        self.document_metadata = {}
        self.idf_scores = {}
        self.load_index()

    def load_index(self):
        try:
            if os.path.exists(app.config['INDEX_FILE']):
                with open(app.config['INDEX_FILE'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.inverted_index = data.get('inverted_index', {})
                    self.documents = data.get('documents', {})
                    self.idf_scores = data.get('idf_scores', {})
                # Fix old format missing token_count
                for doc_id, doc in self.documents.items():
                    if 'token_count' not in doc:
                        doc['token_count'] = len(doc.get('tokens', []))
            if os.path.exists(app.config['METADATA_FILE']):
                with open(app.config['METADATA_FILE'], 'r', encoding='utf-8') as f:
                    self.document_metadata = json.load(f)
            if self.documents:
                self.calculate_idf()
        except Exception as e:
            print(f"Load error: {e}")
            self.inverted_index = {}
            self.documents = {}
            self.document_metadata = {}
            self.idf_scores = {}

    def save_index(self):
        with open(app.config['INDEX_FILE'], 'w', encoding='utf-8') as f:
            json.dump({
                'inverted_index': self.inverted_index,
                'documents': self.documents,
                'idf_scores': self.idf_scores
            }, f, indent=2)
        with open(app.config['METADATA_FILE'], 'w', encoding='utf-8') as f:
            json.dump(self.document_metadata, f, indent=2)

    def extract_text_from_pdf(self, filepath):
        text = ""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += (page.extract_text() or "") + "\n"
        except Exception as e:
            print(f"PDF error: {e}")
        return text

    def extract_text_from_docx(self, filepath):
        text = ""
        try:
            doc = DocxDocument(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"DOCX error: {e}")
        return text

    def extract_text_from_txt(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            print(f"TXT error: {e}")
            return ""

    def extract_text(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            return self.extract_text_from_pdf(filepath)
        elif ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(filepath)
        elif ext == '.txt':
            return self.extract_text_from_txt(filepath)
        return ""

    def tokenize(self, text):
        return re.findall(r'\b[a-z]+\b', text.lower())

    def extract_clauses(self, text):
        clauses = []
        patterns = [
            r'\n\s*\d+\.\s+',
            r'\n\s*\d+\.\d+\s+',
            r'\n\s*Article\s+\d+',
            r'\n\s*Section\s+\d+',
            r'\n\s*Clause\s+\d+',
        ]
        for pattern in patterns:
            parts = re.split(pattern, text)
            if len(parts) > 1:
                clauses = [p.strip() for p in parts if p.strip()]
                break
        if not clauses:
            clauses = [p.strip() for p in text.split('\n\n') if p.strip()]
        return [c[:500] + '...' if len(c) > 500 else c for c in clauses]

    def add_document(self, doc_id, filepath, filename):
        text = self.extract_text(filepath)
        if not text.strip():
            return False, "Could not extract text from document"
        clauses = self.extract_clauses(text)
        tokens = self.tokenize(text)
        self.documents[doc_id] = {
            'filename': filename,
            'filepath': filepath,
            'text': text,
            'clauses': clauses,
            'tokens': tokens,
            'token_count': len(tokens)
        }
        self.document_metadata[doc_id] = {
            'filename': filename,
            'upload_date': datetime.now().isoformat(),
            'file_size': os.path.getsize(filepath),
            'num_clauses': len(clauses),
            'num_tokens': len(tokens)
        }
        token_freq = Counter(tokens)
        for token, freq in token_freq.items():
            if token not in self.inverted_index:
                self.inverted_index[token] = {}
            self.inverted_index[token][doc_id] = {
                'tf': freq,
                'positions': [i for i, t in enumerate(tokens) if t == token]
            }
        self.calculate_idf()
        self.save_index()
        return True, "Document indexed successfully"

    def delete_document(self, doc_id):
        if doc_id not in self.documents:
            return False, "Document not found"
        filepath = self.documents[doc_id]['filepath']
        for token in list(self.inverted_index.keys()):
            if doc_id in self.inverted_index[token]:
                del self.inverted_index[token][doc_id]
            if not self.inverted_index[token]:
                del self.inverted_index[token]
        del self.documents[doc_id]
        if doc_id in self.document_metadata:
            del self.document_metadata[doc_id]
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Delete error: {e}")
        self.calculate_idf()
        self.save_index()
        return True, "Document deleted successfully"

    def calculate_idf(self):
        total_docs = len(self.documents)
        if total_docs == 0:
            self.idf_scores = {}
            return
        for term, postings in self.inverted_index.items():
            doc_freq = len(postings)
            # Smoothed IDF - never returns 0
            self.idf_scores[term] = math.log((total_docs + 1) / (doc_freq + 1)) + 1

    def calculate_tf_idf(self, doc_id, term):
        if term not in self.inverted_index or doc_id not in self.inverted_index[term]:
            return 0
        tf = self.inverted_index[term][doc_id]['tf']
        idf = self.idf_scores.get(term, 0)
        doc_length = self.documents[doc_id].get('token_count', 1) or 1
        normalized_tf = tf / doc_length
        return normalized_tf * idf

    def boolean_search(self, query):
        query = query.lower()
        if ' and ' in query:
            terms = [t.strip() for t in query.split(' and ')]
            result_sets = []
            for term in terms:
                term_docs = set()
                for token in self.tokenize(term):
                    if token in self.inverted_index:
                        term_docs.update(self.inverted_index[token].keys())
                result_sets.append(term_docs)
            return set.intersection(*result_sets) if result_sets else set()
        elif ' or ' in query:
            result_docs = set()
            for term in query.split(' or '):
                for token in self.tokenize(term.strip()):
                    if token in self.inverted_index:
                        result_docs.update(self.inverted_index[token].keys())
            return result_docs
        elif ' not ' in query:
            parts = query.split(' not ', 1)
            include_docs = set()
            for token in self.tokenize(parts[0].strip()):
                if token in self.inverted_index:
                    include_docs.update(self.inverted_index[token].keys())
            exclude_docs = set()
            for token in self.tokenize(parts[1].strip()):
                if token in self.inverted_index:
                    exclude_docs.update(self.inverted_index[token].keys())
            return include_docs - exclude_docs
        else:
            result_docs = set()
            for token in self.tokenize(query):
                if token in self.inverted_index:
                    result_docs.update(self.inverted_index[token].keys())
            return result_docs

    # ================================================================
    # BUILD ALL 7 IR TABLES
    # ================================================================
    def build_ir_tables(self, query, matched_docs):
        query_tokens = self.tokenize(query)
        if not query_tokens or not self.documents:
            return {}

        # Unique query tokens
        seen, uq = set(), []
        for t in query_tokens:
            if t not in seen:
                seen.add(t)
                uq.append(t)

        doc_ids = list(self.documents.keys())
        filenames = {d: self.documents[d]['filename'] for d in doc_ids}

        # --- Table 1: Inverted Index ---
        inverted_index_table = []
        for tok in uq:
            postings = self.inverted_index.get(tok, {})
            inverted_index_table.append({
                'term': tok,
                'documents': [filenames[d] for d in sorted(postings.keys()) if d in filenames],
                'doc_freq': len(postings)
            })

        # --- Table 2: Boolean Retrieval ---
        boolean_table = []
        for d in doc_ids:
            boolean_table.append({
                'doc_id': d,
                'filename': filenames[d],
                'matched': d in matched_docs
            })

        # --- Tables 3, 4, 5: TF, IDF, TF-IDF ---
        tf_table = []
        idf_table = []
        tfidf_table = []

        for tok in uq:
            idf_val = round(self.idf_scores.get(tok, 0), 4)
            idf_table.append({'term': tok, 'idf': idf_val})

            tf_row = {'term': tok, 'values': []}
            tfidf_row = {'term': tok, 'values': []}

            for d in doc_ids:
                doc_len = self.documents[d].get('token_count', 1) or 1
                raw_tf = self.inverted_index.get(tok, {}).get(d, {})
                if isinstance(raw_tf, dict):
                    raw_tf = raw_tf.get('tf', 0)
                else:
                    raw_tf = 0
                tf_val = round(raw_tf / doc_len, 4)
                tfidf_val = round(tf_val * idf_val, 4)

                tf_row['values'].append({
                    'doc_id': d,
                    'filename': filenames[d],
                    'value': tf_val
                })
                tfidf_row['values'].append({
                    'doc_id': d,
                    'filename': filenames[d],
                    'value': tfidf_val
                })

            tf_table.append(tf_row)
            tfidf_table.append(tfidf_row)

        # --- Table 6: Cosine Similarity ---
        q_len = len(query_tokens) or 1
        q_tf_count = Counter(query_tokens)
        cosine_table = []

        for d in doc_ids:
            dot = 0.0
            q_mag = 0.0
            d_mag = 0.0
            for tok in uq:
                idf = self.idf_scores.get(tok, 0)
                q_tf = (q_tf_count[tok] / q_len) * idf
                doc_len = self.documents[d].get('token_count', 1) or 1
                raw = self.inverted_index.get(tok, {}).get(d, {})
                raw_tf = raw.get('tf', 0) if isinstance(raw, dict) else 0
                d_tf = (raw_tf / doc_len) * idf
                dot   += q_tf * d_tf
                q_mag += q_tf ** 2
                d_mag += d_tf ** 2

            denom = math.sqrt(q_mag) * math.sqrt(d_mag)
            cosine_val = round(dot / denom, 4) if denom > 0 else 0.0
            cosine_table.append({
                'doc_id': d,
                'filename': filenames[d],
                'cosine': cosine_val
            })

        # --- Table 7: Ranking ---
        ranking_table = sorted(
            [{'doc_id': r['doc_id'], 'filename': r['filename'], 'cosine': r['cosine']}
             for r in cosine_table],
            key=lambda x: x['cosine'],
            reverse=True
        )
        for i, row in enumerate(ranking_table):
            row['rank'] = i + 1

        return {
            'doc_ids': doc_ids,
            'filenames': filenames,
            'query_tokens': uq,
            'inverted_index_table': inverted_index_table,
            'boolean_table': boolean_table,
            'tf_table': tf_table,
            'idf_table': idf_table,
            'tfidf_table': tfidf_table,
            'cosine_table': cosine_table,
            'ranking_table': ranking_table
        }

    def search(self, query, top_k=10):
        if not query.strip():
            return [], {}

        candidate_docs = self.boolean_search(query)
        query_tokens = self.tokenize(query)

        # Build IR tables for ALL docs
        ir_tables = self.build_ir_tables(query, candidate_docs)

        if not candidate_docs:
            return [], ir_tables

        scores = {}
        for doc_id in candidate_docs:
            score = sum(self.calculate_tf_idf(doc_id, token) for token in query_tokens)
            scores[doc_id] = score

        ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in ranked_docs[:top_k]:
            doc = self.documents[doc_id]
            metadata = self.document_metadata[doc_id]
            relevant_clauses = [
                clause for clause in doc['clauses']
                if any(token in clause.lower() for token in query_tokens)
            ][:3]
            results.append({
                'doc_id': doc_id,
                'filename': doc['filename'],
                'score': round(score * 100, 2),
                'clauses': relevant_clauses,
                'upload_date': metadata['upload_date'],
                'num_clauses': metadata['num_clauses']
            })

        return results, ir_tables

    def get_all_documents(self):
        return [
            {
                'doc_id': doc_id,
                'filename': metadata['filename'],
                'upload_date': metadata['upload_date'],
                'file_size': metadata['file_size'],
                'num_clauses': metadata['num_clauses'],
                'num_tokens': metadata['num_tokens']
            }
            for doc_id, metadata in self.document_metadata.items()
        ]


search_engine = LegalDocumentSearchEngine()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'No files uploaded'})
    files = request.files.getlist('files')
    results = []
    for file in files:
        if file.filename == '':
            continue
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{doc_id}_{filename}")
        file.save(filepath)
        success, message = search_engine.add_document(doc_id, filepath, filename)
        results.append({'filename': filename, 'success': success, 'message': message})
    return jsonify({'success': True, 'results': results})


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '')
    if not query.strip():
        return jsonify({'success': False, 'message': 'Please enter a search query'})
    results, ir_tables = search_engine.search(query)
    return jsonify({
        'success': True,
        'query': query,
        'results': results,
        'ir_tables': ir_tables      # <-- sent to frontend
    })


@app.route('/documents', methods=['GET'])
def get_documents():
    return jsonify({'success': True, 'documents': search_engine.get_all_documents()})


@app.route('/delete/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    success, message = search_engine.delete_document(doc_id)
    return jsonify({'success': success, 'message': message})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)