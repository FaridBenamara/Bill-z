import { useState, useEffect, useRef } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import api from '../services/api';
import { 
  CreditCard, 
  Upload, 
  Download, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  XCircle,
  TrendingUp,
  TrendingDown,
  FileSpreadsheet
} from 'lucide-react';

function Transactions({ setAuth }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ total: 0, income: 0, expenses: 0, reconciled: 0 });
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/transactions/');
      setTransactions(response.data);
      calculateStats(response.data);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement des transactions');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (txs) => {
    const total = txs.length;
    const income = txs.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0);
    const expenses = Math.abs(txs.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0));
    const reconciled = txs.filter(t => t.is_reconciled).length;
    setStats({ total, income, expenses, reconciled });
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Vérifier l'extension
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      setUploadResult({
        success: false,
        message: 'Format non supporté. Utilisez CSV ou Excel (.xlsx, .xls)'
      });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      setUploadResult(null);
      const response = await api.post('/api/transactions/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setUploadResult({
        success: true,
        message: response.data.message
      });
      
      // Recharger les transactions
      await loadTransactions();
    } catch (err) {
      setUploadResult({
        success: false,
        message: err.response?.data?.detail || 'Erreur lors de l\'upload'
      });
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const deleteTransaction = async (transactionId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette transaction ?')) {
      return;
    }

    try {
      await api.delete(`/api/transactions/${transactionId}`);
      setTransactions(transactions.filter(t => t.id !== transactionId));
      calculateStats(transactions.filter(t => t.id !== transactionId));
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  };

  const formatAmount = (amount) => {
    const formatted = Math.abs(amount).toFixed(2);
    return amount >= 0 ? `+${formatted} €` : `-${formatted} €`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  return (
    <DashboardLayout setAuth={setAuth}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Transactions bancaires</h1>
            <p className="text-muted-foreground mt-1">
              {stats.total} transaction{stats.total > 1 ? 's' : ''} importée{stats.total > 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn-primary flex items-center gap-2"
              disabled={uploading}
            >
              <Upload size={20} className={uploading ? 'animate-pulse' : ''} />
              {uploading ? 'Upload en cours...' : 'Importer CSV/Excel'}
            </button>
            <button
              onClick={loadTransactions}
              className="btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
              Actualiser
            </button>
          </div>
        </div>

        {/* Upload Result */}
        {uploadResult && (
          <div className={`p-4 rounded-lg border ${
            uploadResult.success 
              ? 'bg-green-500/10 border-green-500 text-green-500' 
              : 'bg-red-500/10 border-red-500 text-red-500'
          }`}>
            {uploadResult.message}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="text-2xl font-bold text-foreground">{stats.total}</p>
              </div>
              <CreditCard className="text-primary" size={32} />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Recettes</p>
                <p className="text-2xl font-bold text-green-500">+{stats.income.toFixed(2)} €</p>
              </div>
              <TrendingUp className="text-green-500" size={32} />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Dépenses</p>
                <p className="text-2xl font-bold text-red-500">-{stats.expenses.toFixed(2)} €</p>
              </div>
              <TrendingDown className="text-red-500" size={32} />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Rapprochées</p>
                <p className="text-2xl font-bold text-foreground">
                  {stats.reconciled}/{stats.total}
                </p>
              </div>
              <CheckCircle className="text-primary" size={32} />
            </div>
          </div>
        </div>

        {/* Transactions Table */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-lg">
            {error}
          </div>
        ) : transactions.length === 0 ? (
          <div className="card">
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <FileSpreadsheet className="mx-auto text-muted-foreground mb-4" size={64} />
                <h3 className="text-xl font-semibold text-foreground mb-2">Aucune transaction</h3>
                <p className="text-muted-foreground mb-4">
                  Importez vos transactions bancaires au format CSV ou Excel
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-primary flex items-center gap-2 mx-auto"
                >
                  <Upload size={20} />
                  Importer un fichier
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Fournisseur/Client
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Catégorie
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase">
                      Montant
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-muted-foreground uppercase">
                      Statut
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {formatDate(transaction.date)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          {transaction.amount < 0 ? (
                            <TrendingDown className="w-4 h-4 mr-2 text-red-500" />
                          ) : (
                            <TrendingUp className="w-4 h-4 mr-2 text-green-500" />
                          )}
                          <span className="font-medium">{transaction.vendor || 'N/A'}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground max-w-xs truncate">
                        {transaction.description || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {transaction.category ? (
                          <span className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs">
                            {transaction.category}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold">
                        <span className={transaction.amount >= 0 ? 'text-green-500' : 'text-red-500'}>
                          {formatAmount(transaction.amount)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {transaction.is_reconciled ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-500">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Rapprochée
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-500/10 text-gray-500">
                            <XCircle className="w-3 h-3 mr-1" />
                            Non rapprochée
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => deleteTransaction(transaction.id)}
                          className="p-2 hover:bg-red-500/10 rounded-lg transition-colors text-red-500"
                          title="Supprimer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Info Box */}
        {transactions.length > 0 && (
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
            <div className="text-sm text-blue-400">
              💡 <strong>Astuce :</strong> Allez dans la page Factures pour lancer le rapprochement bancaire automatique entre vos factures et transactions.
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default Transactions;


