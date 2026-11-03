import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  FileText,
  UploadCloud,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Plus,
  FileCode,
  ArrowRight,
  Database,
  Layers,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { EmptyState } from '../../components/common/EmptyState';
import { PageLoading } from '../../components/common/Spinner';
import { useToast } from '../../components/common/Toast';
import { documentsApi } from '../../api/documents.api';
import type { DocumentItem, DocumentProcessingStatus } from '../../types';

export const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { error, success, info } = useToast();

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Fetch list of documents
  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.listDocuments(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (docId: string) => documentsApi.deleteDocument(docId),
    onSuccess: () => {
      success('Document removed from knowledge base.');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || 'Failed to delete document.';
      error(msg);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (!title) {
        setTitle(file.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      error('Please select a file to upload.');
      return;
    }
    if (!title.trim()) {
      error('Please provide a document title.');
      return;
    }

    setIsUploading(true);
    try {
      await documentsApi.uploadDocument(selectedFile, title.trim(), description.trim() || undefined);
      success('Document uploaded! Processing embeddings and text chunks...');
      setIsUploadOpen(false);
      setTitle('');
      setDescription('');
      setSelectedFile(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Failed to upload document.';
      error(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const statusVariant = (status: DocumentProcessingStatus) => {
    if (status === 'ready') return 'success';
    if (status === 'processing') return 'warning';
    if (status === 'failed') return 'error';
    return 'default';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (isLoading) {
    return <PageLoading label="Loading RAG knowledge base documents..." />;
  }

  const documents = data?.documents ?? [];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">RAG Documents & Knowledge Base</h1>
          <p className="text-sm text-text-muted mt-0.5">
            Upload architecture specs, project designs, or your resume to power grounded AI interviews.
          </p>
        </div>

        <Button
          id="open-upload-doc-modal-btn"
          onClick={() => setIsUploadOpen(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Upload Document
        </Button>
      </div>

      {/* Document Grid */}
      {documents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc, idx) => (
            <motion.div
              key={doc.document_id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card padding="md" className="space-y-3 relative group">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center shrink-0">
                      <FileCode className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <h2 className="text-sm font-semibold text-text-primary truncate max-w-xs">
                        {doc.title}
                      </h2>
                      <p className="text-xs text-text-muted">
                        {doc.file_type.toUpperCase()} · {formatFileSize(doc.file_size)}
                      </p>
                    </div>
                  </div>

                  <Badge variant={statusVariant(doc.status)} size="sm">
                    {doc.status}
                  </Badge>
                </div>

                {doc.description && (
                  <p className="text-xs text-text-secondary line-clamp-2">{doc.description}</p>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-border text-xs text-text-muted">
                  <span>{doc.chunk_count} vector chunks generated</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => deleteMutation.mutate(doc.document_id)}
                      className="p-1.5 text-text-muted hover:text-error hover:bg-error/10 rounded-lg transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => navigate('/interviews/new')}
                      className="text-xs text-accent hover:underline flex items-center gap-1 font-medium"
                    >
                      Interview on this <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={FileText}
          title="No documents uploaded yet"
          description="Upload technical architecture documents, API specs, or your resume to generate hyper-specific interview questions."
          action={
            <Button onClick={() => setIsUploadOpen(true)} leftIcon={<UploadCloud className="w-4 h-4" />}>
              Upload First Document
            </Button>
          }
        />
      )}

      {/* Upload Modal */}
      <Modal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} title="Upload Knowledge Document">
        <form onSubmit={handleUploadSubmit} className="space-y-4 pt-2">
          {/* File Picker */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Select Document (PDF, TXT, MD, DOCX)
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-border hover:border-accent/60 rounded-2xl p-6 text-center cursor-pointer bg-slate-900/30 transition-all"
            >
              <UploadCloud className="w-8 h-8 text-accent mx-auto mb-2" />
              {selectedFile ? (
                <div>
                  <p className="text-sm font-semibold text-text-primary">{selectedFile.name}</p>
                  <p className="text-xs text-text-muted mt-0.5">{formatFileSize(selectedFile.size)}</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium text-text-secondary">Click or drag file here</p>
                  <p className="text-xs text-text-muted mt-1">PDF, Markdown, Text, or Word documents</p>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md,.markdown,.docx"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Document Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Distributed Database Architecture Spec v2"
              className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl px-4 py-2 text-sm outline-none focus:border-accent"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Description (Optional)
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Architecture RFC outlining sharding, replication topology, and failover mechanics..."
              className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl px-4 py-2 text-sm outline-none focus:border-accent resize-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button variant="ghost" type="button" onClick={() => setIsUploadOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isUploading} leftIcon={<UploadCloud className="w-4 h-4" />}>
              Upload & Vectorize
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
