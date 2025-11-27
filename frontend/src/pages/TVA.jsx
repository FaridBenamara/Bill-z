import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import api from '../services/api';
import { 
  Receipt, 
  Calculator, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  AlertCircle,
  FileText
} from 'lucide-react';

function TVA({ setAuth }) {
  const [loading, setLoading] = useState(true);
  const [tvaData, setTvaData] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTVAData();
  }, []);

  const loadTVAData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [tvaRes, invoicesRes] = await Promise.all([
        api.get('/api/optimisation/tva'),
        api.get('/api/invoices/')
      ]);
      
      setTvaData(tvaRes.data);
      setInvoices(invoicesRes.data);
    } catch (err) {
      setError('Erreur lors du chargement des données TVA');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Grouper les factures par taux de TVA
  const getInvoicesByTVARate = () => {
    const grouped = {};
    invoices.forEach(inv => {
      const rate = inv.amounts?.tva_rate || 0;
      if (!grouped[rate]) {
        grouped[rate] = {
          rate,
          count: 0,
          totalHT: 0,
          totalTVA: 0,
          totalTTC: 0
        };
      }
      grouped[rate].count++;
      grouped[rate].totalHT += inv.amounts?.ht || 0;
      grouped[rate].totalTVA += inv.amounts?.tva || 0;
      grouped[rate].totalTTC += inv.amounts?.ttc || 0;
    });
    return Object.values(grouped).sort((a, b) => b.rate - a.rate);
  };

  if (loading) {
    return (
      <DashboardLayout setAuth={setAuth}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout setAuth={setAuth}>
        <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-lg">
          {error}
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout setAuth={setAuth}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">TVA</h1>
            <p className="text-muted-foreground mt-1">Calculs et déclarations TVA automatiques</p>
          </div>
          <button 
            onClick={loadTVAData}
            className="btn-secondary flex items-center gap-2"
            disabled={loading}
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            Actualiser
          </button>
        </div>

        {/* Cards principales */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card glow-secondary">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-muted-foreground">TVA collectée</p>
              <TrendingUp className="text-green-500" size={20} />
            </div>
            <p className="text-3xl font-bold text-green-500">
              +{tvaData?.tva_collectee?.toFixed(2) || '0.00'} €
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Sur vos ventes (factures émises)
            </p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-muted-foreground">TVA déductible</p>
              <TrendingDown className="text-blue-500" size={20} />
            </div>
            <p className="text-3xl font-bold text-blue-500">
              -{tvaData?.tva_deductible?.toFixed(2) || '0.00'} €
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Sur vos achats (factures reçues)
            </p>
          </div>

          <div className={`card ${tvaData?.tva_a_payer > 0 ? 'glow-primary border-primary' : 'border-green-500'}`}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-muted-foreground">TVA à payer</p>
              <Calculator className={tvaData?.tva_a_payer > 0 ? 'text-red-500' : 'text-green-500'} size={20} />
            </div>
            <p className={`text-3xl font-bold ${tvaData?.tva_a_payer > 0 ? 'text-red-500' : 'text-green-500'}`}>
              {tvaData?.tva_a_payer > 0 ? '-' : '+'}{Math.abs(tvaData?.tva_a_payer || 0).toFixed(2)} €
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {tvaData?.tva_a_payer > 0 ? 'À verser à l\'État' : 'Crédit de TVA'}
            </p>
          </div>
        </div>

        {/* Conseil */}
        {tvaData?.conseil && (
          <div className={`card ${tvaData?.tva_a_payer > 0 ? 'bg-yellow-500/10 border-yellow-500' : 'bg-blue-500/10 border-blue-500'}`}>
            <div className="flex gap-3">
              <AlertCircle className={tvaData?.tva_a_payer > 0 ? 'text-yellow-500' : 'text-blue-400'} size={24} />
              <div>
                <h3 className="font-semibold text-foreground mb-1">Conseil</h3>
                <p className="text-sm text-muted-foreground">{tvaData.conseil}</p>
              </div>
            </div>
          </div>
        )}

        {/* Détail par taux */}
        {getInvoicesByTVARate().length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Détail par taux de TVA
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Taux
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                      Factures
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">
                      Total HT
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">
                      Total TVA
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">
                      Total TTC
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {getInvoicesByTVARate().map((group, index) => (
                    <tr key={index} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <span className="font-semibold text-foreground">{group.rate}%</span>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {group.count}
                      </td>
                      <td className="px-4 py-3 text-right text-sm">
                        {group.totalHT.toFixed(2)} €
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-semibold text-primary">
                        {group.totalTVA.toFixed(2)} €
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-semibold">
                        {group.totalTTC.toFixed(2)} €
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Info si pas de données */}
        {invoices.length === 0 && (
          <div className="card">
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <Receipt className="mx-auto text-muted-foreground mb-4" size={64} />
                <h3 className="text-xl font-semibold text-foreground mb-2">Aucune donnée TVA</h3>
                <p className="text-muted-foreground mb-4">
                  Les calculs apparaîtront automatiquement avec vos factures
                </p>
                <button 
                  onClick={() => window.location.href = '/factures'}
                  className="btn-primary flex items-center gap-2 mx-auto"
                >
                  <FileText size={20} />
                  Scanner mes factures
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default TVA;


