import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import api from '../services/api';
import { 
  TrendingUp, 
  Lightbulb, 
  AlertCircle, 
  CheckCircle, 
  RefreshCw,
  PieChart,
  DollarSign,
  Users,
  FileText
} from 'lucide-react';

function Optimisation({ setAuth }) {
  const [analysis, setAnalysis] = useState(null);
  const [tvaAnalysis, setTvaAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalysis();
  }, []);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Charger l'analyse complète et la TVA en parallèle
      const [analysisRes, tvaRes] = await Promise.all([
        api.get('/api/optimisation/analyze'),
        api.get('/api/optimisation/tva')
      ]);
      
      setAnalysis(analysisRes.data);
      setTvaAnalysis(tvaRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement de l\'analyse');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const refreshAnalysis = async () => {
    setAnalyzing(true);
    await loadAnalysis();
    setAnalyzing(false);
  };

  return (
    <DashboardLayout setAuth={setAuth}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Optimisation fiscale</h1>
            <p className="text-muted-foreground mt-1">
              Analyse intelligente et recommandations personnalisées
            </p>
          </div>
          <button
            onClick={refreshAnalysis}
            className="btn-primary flex items-center gap-2"
            disabled={analyzing || loading}
          >
            <RefreshCw size={20} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyse en cours...' : 'Actualiser'}
          </button>
        </div>

        {/* Loading */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-lg">
            {error}
          </div>
        ) : !analysis ? (
          <div className="card">
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <TrendingUp className="mx-auto text-muted-foreground mb-4" size={64} />
                <h3 className="text-xl font-semibold text-foreground mb-2">Aucune donnée</h3>
                <p className="text-muted-foreground">
                  Commencez par importer des factures et transactions
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Statistiques globales */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Factures</p>
                    <p className="text-2xl font-bold text-foreground">
                      {analysis.statistiques_globales.nombre_factures_total}
                    </p>
                  </div>
                  <FileText className="text-primary" size={32} />
                </div>
              </div>

              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Fournisseurs</p>
                    <p className="text-2xl font-bold text-foreground">
                      {analysis.statistiques_globales.nombre_fournisseurs}
                    </p>
                  </div>
                  <Users className="text-primary" size={32} />
                </div>
              </div>

              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total</p>
                    <p className="text-2xl font-bold text-foreground">
                      {analysis.statistiques_globales.total_factures.toFixed(2)} €
                    </p>
                  </div>
                  <DollarSign className="text-primary" size={32} />
                </div>
              </div>

              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Rapprochement</p>
                    <p className="text-2xl font-bold text-foreground">
                      {(analysis.statistiques_globales.taux_rapprochement * 100).toFixed(0)}%
                    </p>
                  </div>
                  <PieChart className="text-primary" size={32} />
                </div>
              </div>
            </div>

            {/* TVA */}
            {tvaAnalysis && (
              <div className="card">
                <h3 className="text-lg font-semibold text-foreground mb-4">Analyse TVA</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">TVA Collectée</div>
                    <div className="text-xl font-bold text-green-500">
                      +{tvaAnalysis.tva_collectee} €
                    </div>
                  </div>
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">TVA Déductible</div>
                    <div className="text-xl font-bold text-blue-500">
                      -{tvaAnalysis.tva_deductible} €
                    </div>
                  </div>
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">TVA à Payer</div>
                    <div className={`text-xl font-bold ${tvaAnalysis.tva_a_payer > 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {tvaAnalysis.tva_a_payer > 0 ? '-' : '+'}{Math.abs(tvaAnalysis.tva_a_payer)} €
                    </div>
                  </div>
                </div>
                <div className="mt-4 bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                  <div className="text-sm text-blue-400">
                    💡 {tvaAnalysis.conseil}
                  </div>
                </div>
              </div>
            )}

            {/* Résumé */}
            <div className="card bg-primary/10 border-primary">
              <div className="flex gap-3">
                <Lightbulb className="text-primary flex-shrink-0" size={24} />
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Résumé</h3>
                  <p className="text-sm text-muted-foreground">{analysis.résumé}</p>
                </div>
              </div>
            </div>

            {/* Optimisations Fiscales */}
            {analysis.optimisations_fiscales && analysis.optimisations_fiscales.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  💰 Optimisations Fiscales
                </h3>
                <div className="space-y-4">
                  {analysis.optimisations_fiscales.map((opt, index) => (
                    <div key={index} className={`p-4 rounded-lg border ${
                      opt.priorite === 'haute' ? 'bg-red-500/10 border-red-500/30' :
                      opt.priorite === 'moyenne' ? 'bg-yellow-500/10 border-yellow-500/30' :
                      'bg-blue-500/10 border-blue-500/30'
                    }`}>
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${
                            opt.priorite === 'haute' ? 'bg-red-500 text-white' :
                            opt.priorite === 'moyenne' ? 'bg-yellow-500 text-white' :
                            'bg-blue-500 text-white'
                          }`}>
                            {opt.priorite.toUpperCase()}
                          </span>
                          <span className="text-xs px-2 py-1 bg-muted rounded">{opt.categorie}</span>
                        </div>
                        {opt.economie_potentielle && (
                          <span className="text-sm font-bold text-green-500">
                            💰 {opt.economie_potentielle}
                          </span>
                        )}
                      </div>
                      <h4 className="font-semibold text-foreground mb-1">{opt.titre}</h4>
                      <p className="text-sm text-muted-foreground">{opt.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions Prioritaires */}
            {analysis.actions_prioritaires && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Factures à payer */}
                {analysis.actions_prioritaires.factures_a_payer && analysis.actions_prioritaires.factures_a_payer.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                      ⚠️ Factures à payer
                      <span className="text-sm font-normal text-muted-foreground">
                        ({analysis.actions_prioritaires.factures_a_payer.length})
                      </span>
                    </h3>
                    <div className="space-y-3">
                      {analysis.actions_prioritaires.factures_a_payer.map((facture, index) => (
                        <div key={index} className={`p-3 rounded-lg border ${
                          facture.urgence === 'critique' ? 'bg-red-500/10 border-red-500' :
                          facture.urgence === 'haute' ? 'bg-orange-500/10 border-orange-500' :
                          'bg-blue-500/10 border-blue-500'
                        }`}>
                          <div className="flex items-start justify-between mb-2">
                            <div className="font-semibold text-foreground">{facture.fournisseur}</div>
                            <span className={`text-xs px-2 py-1 rounded font-semibold ${
                              facture.urgence === 'critique' ? 'bg-red-500 text-white' :
                              facture.urgence === 'haute' ? 'bg-orange-500 text-white' :
                              'bg-blue-500 text-white'
                            }`}>
                              {facture.urgence}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div>Montant: <span className="font-semibold text-foreground">{facture.montant.toFixed(2)} €</span></div>
                            <div>Échéance: {new Date(facture.date_echeance).toLocaleDateString('fr-FR')}</div>
                            {facture.jours_retard > 0 && (
                              <div className="text-red-500 font-semibold">
                                ⚠️ Retard de {facture.jours_retard} jours
                              </div>
                            )}
                            <div className="text-xs italic mt-2">{facture.raison}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Clients à relancer */}
                {analysis.actions_prioritaires.clients_a_relancer && analysis.actions_prioritaires.clients_a_relancer.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                      📞 Clients à relancer
                      <span className="text-sm font-normal text-muted-foreground">
                        ({analysis.actions_prioritaires.clients_a_relancer.length})
                      </span>
                    </h3>
                    <div className="space-y-3">
                      {analysis.actions_prioritaires.clients_a_relancer.map((client, index) => (
                        <div key={index} className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                          <div className="flex items-start justify-between mb-2">
                            <div className="font-semibold text-foreground">{client.client}</div>
                            <span className="text-xs px-2 py-1 rounded bg-yellow-500 text-white font-semibold">
                              {client.jours_impaye}j
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div>Montant: <span className="font-semibold text-foreground">{client.montant.toFixed(2)} €</span></div>
                            <div>Émission: {new Date(client.date_emission).toLocaleDateString('fr-FR')}</div>
                            <div className="mt-2">
                              <span className="text-xs px-2 py-1 rounded bg-orange-500 text-white">
                                {client.action_recommandee}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Conseils de trésorerie */}
            {analysis.conseils_tresorerie && analysis.conseils_tresorerie.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  💡 Conseils de trésorerie
                </h3>
                <div className="space-y-3">
                  {analysis.conseils_tresorerie.map((conseil, index) => (
                    <div key={index} className={`p-4 rounded-lg border ${
                      conseil.type === 'alerte' ? 'bg-red-500/10 border-red-500/30' :
                      conseil.type === 'conseil' ? 'bg-blue-500/10 border-blue-500/30' :
                      'bg-green-500/10 border-green-500/30'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">
                          {conseil.type === 'alerte' ? '⚠️' : conseil.type === 'conseil' ? '💡' : '✨'}
                        </span>
                        <h4 className="font-semibold text-foreground">{conseil.titre}</h4>
                      </div>
                      <p className="text-sm text-muted-foreground">{conseil.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Optimisations legacy */}
            {analysis.optimisations && analysis.optimisations.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  💡 Recommandations générales
                </h3>
                <ul className="space-y-3">
                  {analysis.optimisations.map((opt, index) => (
                    <li key={index} className="flex items-start gap-3 p-3 bg-green-500/10 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-foreground">{opt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Anomalies */}
            {analysis.anomalies && analysis.anomalies.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  ⚠️ Anomalies détectées
                </h3>
                <ul className="space-y-3">
                  {analysis.anomalies.map((anomaly, index) => (
                    <li key={index} className="flex items-start gap-3 p-3 bg-yellow-500/10 rounded-lg">
                      <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-foreground">{anomaly}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Analyse par fournisseur */}
            {analysis.analyse_fournisseurs && analysis.analyse_fournisseurs.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  Analyse par fournisseur
                </h3>
                <div className="space-y-4">
                  {analysis.analyse_fournisseurs.slice(0, 5).map((fournisseur, index) => (
                    <div key={index} className="border border-border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="font-semibold text-foreground">{fournisseur.fournisseur}</div>
                        <div className="text-sm text-muted-foreground">
                          {fournisseur.nombre_factures} facture{fournisseur.nombre_factures > 1 ? 's' : ''}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">Total dépenses</div>
                          <div className="font-semibold">{fournisseur.total_depenses.toFixed(2)} €</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Moyenne</div>
                          <div className="font-semibold">{fournisseur.moyenne_depense.toFixed(2)} €</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

export default Optimisation;


