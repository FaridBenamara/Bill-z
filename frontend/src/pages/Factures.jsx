import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import api from '../services/api';
import { FileText, Download, Trash2, AlertCircle, CheckCircle, RefreshCw, Mail, Link as LinkIcon } from 'lucide-react';

function Factures({ setAuth }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [showAnomaliesModal, setShowAnomaliesModal] = useState(false);
  const [showReconciliationModal, setShowReconciliationModal] = useState(false);
  const [reconciliationResult, setReconciliationResult] = useState(null);
  const [reconcilingInvoiceId, setReconcilingInvoiceId] = useState(null);
  const [reconcilingAll, setReconcilingAll] = useState(false);
  const [reconcileAllResult, setReconcileAllResult] = useState(null);

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
    } finally {
      setScanning(false);
    }
  };

  const showAnomalies = (invoice) => {
    setSelectedInvoice(invoice);
    setShowAnomaliesModal(true);
  };

  const reconcileInvoice = async (invoice) => {
    try {
      setReconcilingInvoiceId(invoice.id);
      setSelectedInvoice(invoice);
      const response = await api.post(`/api/transactions/reconcile/${invoice.id}`);
      setReconciliationResult(response.data);
      setShowReconciliationModal(true);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors du rapprochement');
    } finally {
      setReconcilingInvoiceId(null);
    }
  };

  const confirmReconciliation = async (ligne) => {
    if (!ligne.transaction_id) {
      alert(`Erreur: ID de transaction manquant.\n\nDétails de la ligne:\n- Date: ${ligne.date}\n- Montant: ${ligne.amount}\n- Vendor: ${ligne.vendor}\n\nVeuillez contacter le support ou réessayer.`);
      return;
    }

    if (!confirm(`Confirmer le rapprochement avec un niveau de confiance de ${(ligne.niveau_confiance * 100).toFixed(0)}% ?\n\nTransaction: ${ligne.vendor}\nMontant: ${ligne.amount} €\nDate: ${ligne.date}`)) {
      return;
    }

    try {
      const response = await api.post(
        `/api/transactions/reconcile/${selectedInvoice.id}/confirm/${ligne.transaction_id}`,
        null,
        {
          params: {
            confidence: ligne.niveau_confiance
          }
        }
      );

      alert('✓ Rapprochement confirmé avec succès !');
      setShowReconciliationModal(false);
      
      // Recharger les factures pour mettre à jour l'affichage
      await loadInvoices();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la confirmation');
    }
  };

  const reconcileAllInvoices = async () => {
    if (!confirm('Lancer le rapprochement automatique pour toutes les factures ?\n\nLes correspondances avec une confiance ≥ 85% seront confirmées automatiquement.')) {
      return;
    }

    try {
      setReconcilingAll(true);
      setReconcileAllResult(null);
      const response = await api.post('/api/transactions/reconcile-all');
      setReconcileAllResult(response.data);
      
      // Recharger les factures
      await loadInvoices();
      
      alert(`✓ Rapprochement automatique terminé !\n\n${response.data.stats.auto_confirmed} rapprochement(s) confirmé(s)\n${response.data.stats.manual_review} nécessitent une revue manuelle`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors du rapprochement automatique');
    } finally {
      setReconcilingAll(false);
    }
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
              onClick={reconcileAllInvoices}
              className="btn-secondary flex items-center gap-2"
              disabled={reconcilingAll || loading || invoices.length === 0}
            >
              <LinkIcon size={20} className={reconcilingAll ? 'animate-pulse' : ''} />
              {reconcilingAll ? 'Rapprochement...' : 'Rapprocher tout'}
            </button>
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

        {reconcileAllResult && (
          <div className="bg-blue-500/10 border border-blue-500 rounded-lg p-4">
            <div className="font-semibold text-blue-400 mb-2">
              ✓ Rapprochement automatique terminé
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Traitées</div>
                <div className="text-lg font-bold text-foreground">{reconcileAllResult.stats.processed}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Auto-confirmées</div>
                <div className="text-lg font-bold text-green-500">{reconcileAllResult.stats.auto_confirmed}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Revue manuelle</div>
                <div className="text-lg font-bold text-yellow-500">{reconcileAllResult.stats.manual_review}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Sans correspondance</div>
                <div className="text-lg font-bold text-gray-500">{reconcileAllResult.stats.no_match}</div>
              </div>
            </div>
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
                        <div className="flex flex-col gap-1">
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
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => reconcileInvoice(invoice)}
                            className="p-2 hover:bg-green-500/10 rounded-lg transition-colors text-green-500"
                            title="Rapprocher"
                            disabled={reconcilingInvoiceId === invoice.id}
                          >
                            <LinkIcon className={`w-4 h-4 ${reconcilingInvoiceId === invoice.id ? 'animate-pulse' : ''}`} />
                          </button>
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

        {/* Modal Rapprochement Bancaire */}
        {showReconciliationModal && reconciliationResult && selectedInvoice && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto" onClick={() => setShowReconciliationModal(false)}>
            <div className="bg-card border border-border rounded-lg p-6 max-w-4xl w-full mx-4 my-8" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-foreground">Rapprochement bancaire</h3>
                <button
                  onClick={() => setShowReconciliationModal(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  ✕
                </button>
              </div>

              {/* Facture Info */}
              <div className="bg-muted/30 p-4 rounded-lg mb-4">
                <div className="text-sm text-muted-foreground mb-2">Facture analysée</div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-xs text-muted-foreground">Fournisseur</div>
                    <div className="font-semibold">{reconciliationResult.facture.fournisseur}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Montant TTC</div>
                    <div className="font-semibold">{reconciliationResult.facture.montant_ttc} €</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Date</div>
                    <div className="font-semibold">{new Date(reconciliationResult.facture.date).toLocaleDateString('fr-FR')}</div>
                  </div>
                </div>
              </div>

              {/* Résultat */}
              <div className={`p-4 rounded-lg border mb-4 ${
                reconciliationResult.correspondance_trouvee
                  ? 'bg-green-500/10 border-green-500'
                  : 'bg-yellow-500/10 border-yellow-500'
              }`}>
                <div className={`font-semibold ${
                  reconciliationResult.correspondance_trouvee ? 'text-green-500' : 'text-yellow-500'
                }`}>
                  {reconciliationResult.correspondance_trouvee ? '✓ Correspondance trouvée' : '⚠ Aucune correspondance'}
                </div>
                <div className="text-sm mt-1 text-muted-foreground">
                  {reconciliationResult.conclusion}
                </div>
              </div>

              {/* Lignes correspondantes */}
              {reconciliationResult.lignes_correspondantes && reconciliationResult.lignes_correspondantes.length > 0 && (
                <div className="space-y-3">
                  <div className="text-sm font-medium text-foreground">
                    {reconciliationResult.lignes_correspondantes.length} transaction{reconciliationResult.lignes_correspondantes.length > 1 ? 's' : ''} correspondante{reconciliationResult.lignes_correspondantes.length > 1 ? 's' : ''} :
                  </div>
                  {reconciliationResult.lignes_correspondantes.map((ligne, index) => (
                    <div key={index} className="border border-border rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm font-medium text-foreground">
                          Transaction #{index + 1}
                        </div>
                        {ligne.transaction_id && (
                          <div className="text-xs text-muted-foreground">
                            ID: {ligne.transaction_id}
                          </div>
                        )}
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="text-xs text-muted-foreground">Vendor</div>
                          <div className="font-medium">{ligne.vendor}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Montant</div>
                          <div className="font-medium">{ligne.amount} €</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Date</div>
                          <div className="font-medium">{ligne.date}</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="flex-1">
                          <div className="text-xs text-muted-foreground mb-1">Similarité fournisseur</div>
                          <div className="w-full bg-muted rounded-full h-2">
                            <div 
                              className="bg-primary h-2 rounded-full transition-all"
                              style={{ width: `${ligne.similarite_fournisseur * 100}%` }}
                            ></div>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {(ligne.similarite_fournisseur * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div className="flex-1">
                          <div className="text-xs text-muted-foreground mb-1">Niveau de confiance</div>
                          <div className="w-full bg-muted rounded-full h-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full transition-all"
                              style={{ width: `${ligne.niveau_confiance * 100}%` }}
                            ></div>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {(ligne.niveau_confiance * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      {ligne.differences && ligne.differences.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-2">Différences :</div>
                          <ul className="space-y-1">
                            {ligne.differences.map((diff, i) => (
                              <li key={i} className="text-xs text-yellow-500 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                {diff}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {ligne.details_differences && (
                        <div className="bg-muted/30 p-3 rounded text-xs space-y-1">
                          <div className="grid grid-cols-2 gap-2">
                            <div>Écart montant: {ligne.details_differences.ecart_montant} €</div>
                            <div>Écart jours: {ligne.details_differences.ecart_jours}</div>
                          </div>
                        </div>
                      )}

                      <div className="mt-3">
                        {ligne.niveau_confiance >= 0.7 ? (
                          <button
                            onClick={() => confirmReconciliation(ligne)}
                            className="w-full btn-primary flex items-center justify-center gap-2"
                          >
                            <CheckCircle className="w-4 h-4" />
                            Confirmer ce rapprochement ({(ligne.niveau_confiance * 100).toFixed(0)}% confiance)
                          </button>
                        ) : (
                          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 text-center">
                            <div className="text-sm text-yellow-500">
                              ⚠ Niveau de confiance trop faible ({(ligne.niveau_confiance * 100).toFixed(0)}%)
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              Vérifiez manuellement avant de confirmer
                            </div>
                            <button
                              onClick={() => {
                                if (confirm('Le niveau de confiance est faible. Confirmer quand même ?')) {
                                  confirmReconciliation(ligne);
                                }
                              }}
                              className="mt-2 px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-500 rounded-lg text-sm transition-colors"
                            >
                              Confirmer manuellement
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 flex gap-3 justify-end">
                <button
                  onClick={() => setShowReconciliationModal(false)}
                  className="px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                >
                  Fermer
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


