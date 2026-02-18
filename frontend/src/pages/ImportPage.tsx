import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { importApi, ImportTransaction } from '../api/client';
import { CategoryAutocomplete } from '../components/CategoryAutocomplete';

// Simple SVG icons
const UploadIcon = () => (
  <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const FileIcon = () => (
  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const AlertIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XIcon = () => (
  <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CheckLargeIcon = () => (
  <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const HelpIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CheckCircleIcon = () => (
  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const LargeCheckCircleIcon = () => (
  <svg className="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

interface TransactionWithEdit extends ImportTransaction {
  id: string;
  editedCategory?: string;
}

export function ImportPage() {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [bankType, setBankType] = useState<string>('');
  const [transactions, setTransactions] = useState<TransactionWithEdit[]>([]);
  const [preview, setPreview] = useState<{
    total: number;
    high: number;
    medium: number;
    low: number;
    duplicate: number;
    detectedBank: string | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<{imported: number; patterns: number} | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const bankOptions = [
    { value: '', label: t('import.autoDetect') },
    { value: 'tinkoff', label: 'Tinkoff Bank' },
    { value: 'sber', label: 'SberBank' },
    { value: 'alfa', label: 'Alfa-Bank' },
  ];

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      // Check if file is CSV or PDF
      if (droppedFile.name.toLowerCase().endsWith('.csv') || 
          droppedFile.name.toLowerCase().endsWith('.pdf')) {
        setFile(droppedFile);
        setError(null);
        setSuccess(null);
      } else {
        setError(t('import.invalidFileType') || 'Only CSV and PDF files are supported');
      }
    }
  };

  const handlePreview = async () => {
    if (!file) {
      setError(t('import.noFile'));
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await importApi.preview(file, bankType || undefined);
      console.log('Preview response:', response);
      
      if (!response.transactions || !Array.isArray(response.transactions)) {
        throw new Error('Invalid response format');
      }
      
      // Add unique IDs for React keys
      const txsWithId = response.transactions.map((tx, idx) => ({
        ...tx,
        id: `tx-${idx}`,
        editedCategory: tx.suggested_category || undefined,
      }));
      
      setTransactions(txsWithId);
      setPreview({
        total: response.total_count || 0,
        high: response.high_confidence_count || 0,
        medium: response.medium_confidence_count || 0,
        low: response.low_confidence_count || 0,
        duplicate: response.duplicate_count || 0,
        detectedBank: response.detected_bank || null,
      });
    } catch (err: any) {
      console.error('Preview error:', err);
      setError(err.response?.data?.detail || err.message || t('import.previewError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryChange = (txId: string, category: string) => {
    setTransactions(prev => {
      // Find the transaction being edited to get its description
      const targetTx = prev.find(tx => tx.id === txId);
      if (!targetTx) return prev;
      
      const targetDesc = targetTx.raw_description;
      
      // Update category for all transactions with the same description
      return prev.map(tx => {
        if (tx.raw_description === targetDesc) {
          return { ...tx, editedCategory: category };
        }
        return tx;
      });
    });
  };

  const handleDeleteRow = (txId: string) => {
    setTransactions(prev => {
      const filtered = prev.filter(tx => tx.id !== txId);
      // Update preview counts
      const deleted = prev.find(tx => tx.id === txId);
      if (deleted && preview) {
        setPreview({
          ...preview,
          total: preview.total - 1,
          high: deleted.confidence === 'high' ? preview.high - 1 : preview.high,
          medium: deleted.confidence === 'medium' ? preview.medium - 1 : preview.medium,
          low: deleted.confidence === 'low' ? preview.low - 1 : preview.low,
          duplicate: deleted.is_duplicate ? preview.duplicate - 1 : preview.duplicate,
        });
      }
      return filtered;
    });
  };

  const handleImport = async () => {
    setIsImporting(true);
    setError(null);

    try {
      // Prepare transactions with edited categories
      const txsToImport = transactions.map(tx => ({
        ...tx,
        suggested_category: tx.editedCategory || tx.suggested_category || 'Other',
      }));

      const result = await importApi.confirm(txsToImport, true);
      
      setImportResult({
        imported: result.imported_count,
        patterns: result.saved_patterns,
      });
      
      setSuccess(t('import.success', { count: result.imported_count }));
      
      // Clear preview after successful import
      setTransactions([]);
      setPreview(null);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('import.importError'));
    } finally {
      setIsImporting(false);
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <div className="text-green-600"><CheckIcon /></div>;
      case 'medium':
        return <div className="text-yellow-600"><HelpIcon /></div>;
      case 'low':
        return <div className="text-red-600"><AlertIcon /></div>;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('import.title')}</h1>

      {/* Upload Section */}
      {!preview && !importResult && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="space-y-6">
            {/* File Upload with Drag & Drop */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('import.fileLabel')}
              </label>
              <div className="flex items-center gap-4">
                <div 
                  className="flex-1"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <label className="cursor-pointer block">
                    <div className={`flex items-center justify-center w-full h-32 px-4 transition border-2 border-dashed rounded-lg ${
                      isDragging 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-300 bg-white hover:border-blue-500 hover:bg-blue-50'
                    }`}>
                      <div className="flex flex-col items-center">
                        <UploadIcon />
                        <span className="text-sm text-gray-500">
                          {file ? file.name : t('import.dropzone')}
                        </span>
                        {isDragging && (
                          <span className="text-sm text-blue-600 mt-1 font-medium">
                            {t('import.dropHere') || 'Drop file here'}
                          </span>
                        )}
                      </div>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,.pdf"
                      className="hidden"
                      onChange={handleFileSelect}
                    />
                  </label>
                </div>
              </div>
            </div>

            {/* Bank Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('import.bankType')}
              </label>
              <select
                value={bankType}
                onChange={(e) => setBankType(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                {bankOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Preview Button */}
            <button
              onClick={handlePreview}
              disabled={!file || isLoading}
              className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  {t('import.parsing')}
                </>
              ) : (
                <>
                  <FileIcon />
                  {t('import.preview')}
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-800">
          <XIcon />
          {error}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center text-green-800">
          <CheckLargeIcon />
          {success}
        </div>
      )}

      {/* Preview Results */}
      {preview && (
        <div className="space-y-6">
          {/* Stats */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('import.previewResults')}</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600">{preview.total}</div>
                <div className="text-sm text-blue-800">{t('import.totalTransactions')}</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">{preview.high}</div>
                <div className="text-sm text-green-800">{t('import.highConfidence')}</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-yellow-600">{preview.medium}</div>
                <div className="text-sm text-yellow-800">{t('import.mediumConfidence')}</div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-red-600">{preview.low}</div>
                <div className="text-sm text-red-800">{t('import.lowConfidence')}</div>
              </div>
              <div className={`p-4 rounded-lg text-center ${preview.duplicate > 0 ? 'bg-orange-50' : 'bg-gray-50'}`}>
                <div className={`text-2xl font-bold ${preview.duplicate > 0 ? 'text-orange-600' : 'text-gray-600'}`}>{preview.duplicate}</div>
                <div className={`text-sm ${preview.duplicate > 0 ? 'text-orange-800' : 'text-gray-800'}`}>{t('import.duplicates')}</div>
              </div>
            </div>

            {preview.detectedBank && (
              <div className="mt-4 text-sm text-gray-600">
                {t('import.detectedBank')}: <span className="font-medium">{preview.detectedBank}</span>
              </div>
            )}
          </div>

          {/* Transactions Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-medium text-gray-900">{t('import.reviewTransactions')}</h3>
              <p className="text-sm text-gray-600 mt-1">{t('import.reviewHint')}</p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('import.date')}
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      {t('import.amount')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('import.description')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('import.category')}
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      {t('import.confidenceColumn')}
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      {t('common.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((tx) => (
                    <tr key={tx.id} className={
                      tx.is_duplicate ? 'bg-orange-50 border-l-4 border-orange-400' : 
                      tx.confidence === 'low' ? 'bg-red-50' : ''
                    }>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {tx.transaction_date 
                          ? new Date(tx.transaction_date).toLocaleString() 
                          : '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium">
                        <span className={tx.type === 'income' ? 'text-green-600' : 'text-red-600'}>
                          {tx.type === 'income' ? '+' : '-'}
                          {tx.amount.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 max-w-xs">
                        <div className="flex items-center gap-2">
                          <span className="truncate" title={tx.raw_description}>
                            {tx.raw_description}
                          </span>
                          {tx.is_duplicate && (
                            <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800" title={t('import.duplicateTooltip')}>
                              ⚠️ {t('import.duplicate')}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <CategoryAutocomplete
                          value={tx.editedCategory ?? tx.suggested_category ?? ''}
                          onChange={(category) => handleCategoryChange(tx.id, category)}
                          placeholder={t('transaction.searchCategory')}
                        />
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center gap-2">
                          {getConfidenceIcon(tx.confidence)}
                          <span className={`px-2 py-1 text-xs rounded-full border ${getConfidenceColor(tx.confidence)}`}>
                            {t(`import.confidence.${tx.confidence}`)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => handleDeleteRow(tx.id)}
                          className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                          title={t('import.deleteRow')}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => {
                setPreview(null);
                setTransactions([]);
                setFile(null);
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              {t('common.cancel')}
            </button>
            <button
              onClick={handleImport}
              disabled={isImporting}
              className="flex-1 flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-300"
            >
              {isImporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  {t('import.importing')}
                </>
              ) : (
                <>
                  <CheckCircleIcon />
                  {t('import.confirmImport', { count: preview.total })}
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Import Result */}
      {importResult && (
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <LargeCheckCircleIcon />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {t('import.completed')}
          </h2>
          <p className="text-gray-600 mb-6">
            {t('import.resultMessage', { 
              imported: importResult.imported, 
              patterns: importResult.patterns 
            })}
          </p>
          <button
            onClick={() => {
              setImportResult(null);
              setSuccess(null);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            {t('import.importAnother')}
          </button>
        </div>
      )}
    </div>
  );
}
