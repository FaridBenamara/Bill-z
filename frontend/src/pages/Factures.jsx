import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import api from '../services/api';
import { FileText, Download, Trash2, AlertCircle, CheckCircle, RefreshCw, Mail } from 'lucide-react';

function Factures({ setAuth }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [showAnomaliesModal, setShowAnomaliesModal] = useState(false);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/invoices/');
      setInvoices(response.data);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement des factures');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const viewPDF = async (invoiceId) => {
    try {
      const response = await api.get(`/api/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      });
      
      // Créer un URL blob et l'ouvrir dans un nouvel onglet
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      
      // Nettoyer l'URL après un délai
      setTimeout(() => window.URL.revokeObjectURL(url), 100);
    } catch (err) {
      alert('Erreur lors de l\'ouverture du PDF');
      console.error(err);
    }
  };

  const deleteInvoice = async (invoiceId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette facture ?')) {
      return;
    }

    try {
      await api.delete(`/api/invoices/${invoiceId}`);
      setInvoices(invoices.filter(inv => inv.id !== invoiceId));
    } catch (err) {
      alert('Erreur lors de la suppression');
      console.error(err);
    }
  };

  const scanGmailInvoices = async () => {
    if (!confirm('Lancer le scan de Gmail pour extraire les factures ?')) {
      return;
    }

    try {
      setScanning(true);
      setScanResult(null);
      const response = await api.post('/api/invoices/scan');
      setScanResult({
        success: true,
        message: `${response.data.invoices_uploaded} facture(s) extraite(s) et ajoutée(s)`
      });
      // Recharger la liste
      await loadInvoices();
    } catch (err) {
      setScanResult({
        success: false,
        message: 'Erreur lors du scan Gmail'
      });
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  const showAnomalies = (invoice) => {
    setSelectedInvoice(invoice);
    setShowAnomaliesModal(true);
  };

  return (
    <DashboardLayout setAuth={setAuth}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Mes Factures</h1>
            <p className="text-muted-foreground mt-1">
              {invoices.length} facture{invoices.length > 1 ? 's' : ''} extraite{invoices.length > 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={scanGmailInvoices}
              className="btn-primary flex items-center gap-2"
              disabled={scanning || loading}
            >
              <Mail size={20} className={scanning ? 'animate-pulse' : ''} />
              {scanning ? 'Scan en cours...' : 'Scanner Gmail'}
            </button>
            <button
              onClick={loadInvoices}
              className="btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
              Actualiser
            </button>
          </div>
        </div>

        {scanResult && (
          <div className={`p-4 rounded-lg border ${
            scanResult.success 
              ? 'bg-green-500/10 border-green-500 text-green-500' 
              : 'bg-red-500/10 border-red-500 text-red-500'
          }`}>
            {scanResult.message}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-lg">
            {error}
          </div>
        ) : invoices.length === 0 ? (
          <div className="card">
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <FileText className="mx-auto text-muted-foreground mb-4" size={64} />
                <h3 className="text-xl font-semibold text-foreground mb-2">Aucune facture</h3>
                <p className="text-muted-foreground">
                  Les factures extraites par l'agent apparaîtront ici
                </p>
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
                      N° Facture
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Fournisseur
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      HT
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      TVA
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      TTC
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Statut
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText className="w-4 h-4 mr-2 text-primary" />
                          <span className="font-medium">{invoice.invoice_number}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {new Date(invoice.invoice_date).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <div className="font-medium">{invoice.supplier.name}</div>
                          {invoice.category && (
                            <div className="text-xs text-muted-foreground">{invoice.category}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {invoice.amounts.ht.toFixed(2)} €
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {invoice.amounts.tva.toFixed(2)} € ({invoice.amounts.tva_rate}%)
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                        {invoice.amounts.ttc.toFixed(2)} €
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {invoice.anomalies && invoice.anomalies.length > 0 ? (
                          <button
                            onClick={() => showAnomalies(invoice)}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20 transition-colors cursor-pointer"
                          >
                            <AlertCircle className="w-3 h-3 mr-1" />
                            {invoice.anomalies.length} anomalie{invoice.anomalies.length > 1 ? 's' : ''}
                          </button>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-500">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Valide
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => viewPDF(invoice.id)}
                            className="p-2 hover:bg-primary/10 rounded-lg transition-colors text-primary"
                            title="Voir le PDF"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => deleteInvoice(invoice.id)}
                            className="p-2 hover:bg-red-500/10 rounded-lg transition-colors text-red-500"
                            title="Supprimer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal Anomalies */}
        {showAnomaliesModal && selectedInvoice && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAnomaliesModal(false)}>
            <div className="bg-card border border-border rounded-lg p-6 max-w-2xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-foreground">Anomalies détectées</h3>
                <button
                  onClick={() => setShowAnomaliesModal(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-muted/30 p-4 rounded-lg">
                  <div className="text-sm text-muted-foreground mb-2">Facture</div>
                  <div className="font-semibold">{selectedInvoice.invoice_number || 'N/A'}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {selectedInvoice.supplier.name} - {selectedInvoice.amounts.ttc.toFixed(2)} €
                  </div>
                </div>

                <div>
                  <div className="text-sm font-medium text-foreground mb-3">
                    {selectedInvoice.anomalies.length} anomalie{selectedInvoice.anomalies.length > 1 ? 's' : ''} :
                  </div>
                  <ul className="space-y-2">
                    {selectedInvoice.anomalies.map((anomaly, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <span className="text-muted-foreground">{anomaly}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                  <div className="text-sm text-blue-400">
                    💡 <strong>Conseil :</strong> Ces anomalies n'empêchent pas l'utilisation de la facture mais peuvent nécessiter une vérification manuelle.
                  </div>
                </div>
              </div>

              <div className="mt-6 flex gap-3 justify-end">
                <button
                  onClick={() => setShowAnomaliesModal(false)}
                  className="px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                >
                  Fermer
                </button>
                <button
                  onClick={() => {
                    viewPDF(selectedInvoice.id);
                    setShowAnomaliesModal(false);
                  }}
                  className="px-4 py-2 bg-primary hover:bg-primary/80 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Voir le PDF
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default Factures;


