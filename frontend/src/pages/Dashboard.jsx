import { useState, useEffect } from 'react';
import { 
  FileText, 
  CreditCard, 
  TrendingUp, 
  TrendingDown,
  AlertCircle,
  RefreshCw
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import DashboardLayout from '../components/DashboardLayout'
import api from '../services/api'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function Dashboard({ setAuth }) {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [statsRes, invoicesRes, transactionsRes] = await Promise.all([
        api.get('/api/optimisation/stats'),
        api.get('/api/invoices/'),
        api.get('/api/transactions/')
      ]);
      
      setStats(statsRes.data);
      setInvoices(invoicesRes.data.slice(0, 5)); // 5 dernières
      setTransactions(transactionsRes.data.slice(0, 5)); // 5 dernières
    } catch (err) {
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  // Calculer les totaux
  const totalRevenus = (transactions || [])
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);

  const totalDepenses = Math.abs(
    (transactions || [])
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + t.amount, 0)
  );

  // Données pour le graphique par catégorie
  const getCategoryData = () => {
    if (!invoices || invoices.length === 0) return [];
    
    const categories = {};
    invoices.forEach(inv => {
      const cat = inv.category || 'Non catégorisé';
      const amount = inv.amounts?.ttc || 0;
      categories[cat] = (categories[cat] || 0) + amount;
    });
    return Object.entries(categories).map(([name, value]) => ({ name, value }));
  };

  // Données pour le graphique d'évolution (mock pour l'instant)
  const getChartData = () => {
    if (!transactions || transactions.length === 0) return [];
    
    // Grouper par mois
    const months = {};
    transactions.forEach(t => {
      const date = new Date(t.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!months[monthKey]) {
        months[monthKey] = { revenus: 0, depenses: 0 };
      }
      
      if (t.amount > 0) {
        months[monthKey].revenus += t.amount;
      } else {
        months[monthKey].depenses += Math.abs(t.amount);
      }
    });
    
    // Convertir en tableau et trier
    return Object.entries(months)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-6) // 6 derniers mois
      .map(([month, data]) => ({
        mois: new Date(month + '-01').toLocaleDateString('fr-FR', { month: 'short' }),
        revenus: Math.round(data.revenus),
        depenses: Math.round(data.depenses)
      }));
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
            <p className="text-muted-foreground mt-1">Vue d'ensemble de votre activité</p>
          </div>
          <button
            onClick={loadDashboardData}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={20} />
            Actualiser
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card glow-primary hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Factures</p>
                <p className="text-2xl font-bold text-foreground">
                  {stats?.factures?.total || 0}
                </p>
              </div>
              <div className="bg-primary/20 p-3 rounded-full">
                <FileText className="text-primary" size={24} />
              </div>
            </div>
          </div>

          <div className="card glow-secondary hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Revenus</p>
                <p className="text-2xl font-bold text-success">
                  +{totalRevenus.toFixed(2)} €
                </p>
              </div>
              <div className="bg-success/20 p-3 rounded-full">
                <TrendingUp className="text-success" size={24} />
              </div>
            </div>
          </div>

          <div className="card hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Dépenses</p>
                <p className="text-2xl font-bold text-destructive">
                  -{totalDepenses.toFixed(2)} €
                </p>
              </div>
              <div className="bg-destructive/20 p-3 rounded-full">
                <TrendingDown className="text-destructive" size={24} />
              </div>
            </div>
          </div>

          <div className="card glow-primary hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Bénéfice net</p>
                <p className="text-2xl font-bold text-primary">
                  {(totalRevenus - totalDepenses).toFixed(2)} €
                </p>
              </div>
              <div className="bg-primary/20 p-3 rounded-full">
                <CreditCard className="text-primary" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Graphiques */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Graphique par catégorie */}
          <div className="card">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Dépenses par catégorie
            </h2>
            {getCategoryData().length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getCategoryData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getCategoryData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                Aucune donnée disponible
              </div>
            )}
          </div>

          {/* Stats rapprochement */}
          <div className="card">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Rapprochement bancaire
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                <div>
                  <p className="text-sm text-muted-foreground">Transactions</p>
                  <p className="text-2xl font-bold">{stats?.transactions?.total || 0}</p>
                </div>
                <CreditCard className="text-primary" size={32} />
              </div>
              <div className="flex items-center justify-between p-4 bg-green-500/10 rounded-lg">
                <div>
                  <p className="text-sm text-muted-foreground">Rapprochées</p>
                  <p className="text-2xl font-bold text-green-500">{stats?.transactions?.rapprochées || 0}</p>
                </div>
                <div className="text-2xl font-bold text-green-500">
                  {stats?.transactions?.taux_rapprochement || 0}%
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card glow-secondary hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Revenus ce mois</p>
                <p className="text-2xl font-bold text-success">
                  {totalRevenus.toFixed(2)} €
                </p>
              </div>
              <div className="bg-success/20 p-3 rounded-full">
                <TrendingUp className="text-success" size={24} />
              </div>
            </div>
          </div>

          <div className="card hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Dépenses ce mois</p>
                <p className="text-2xl font-bold text-destructive">
                  {totalDepenses.toFixed(2)} €
                </p>
              </div>
              <div className="bg-destructive/20 p-3 rounded-full">
                <TrendingDown className="text-destructive" size={24} />
              </div>
            </div>
          </div>

          <div className="card glow-primary hover:scale-105 transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Bénéfice net</p>
                <p className="text-2xl font-bold text-primary">
                  {(totalRevenus - totalDepenses).toFixed(2)} €
                </p>
              </div>
              <div className="bg-primary/20 p-3 rounded-full">
                <FileText className="text-primary" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Graphique évolution */}
        {getChartData().length > 0 && (
          <div className="card">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              Évolution revenus / dépenses
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="mois" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: 'var(--radius)',
                    color: 'hsl(var(--foreground))'
                  }}
                />
                <Legend />
                <Bar dataKey="revenus" fill="hsl(var(--success))" name="Revenus" />
                <Bar dataKey="depenses" fill="hsl(var(--destructive))" name="Dépenses" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Factures récentes */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="text-primary" size={20} />
              <h2 className="text-lg font-semibold text-foreground">
                Factures récentes
              </h2>
            </div>
            
            <div className="space-y-3">
              {invoices.length > 0 ? (
                invoices.map((invoice) => (
                  <div 
                    key={invoice.id}
                    className="flex items-center justify-between p-3 bg-muted rounded-lg hover:bg-muted/70 transition-colors cursor-pointer"
                  >
                    <div>
                      <p className="font-medium text-foreground">
                        {invoice.supplier?.name || 'N/A'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {invoice.category || 'Non catégorisé'} • {new Date(invoice.invoice_date).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${
                        invoice.invoice_type === 'sortante' ? 'text-success' : 'text-foreground'
                      }`}>
                        {invoice.invoice_type === 'sortante' ? '+' : ''}{invoice.amounts?.ttc?.toFixed(2) || 0} €
                      </p>
                      <span className={`text-xs px-2 py-1 rounded ${
                        invoice.invoice_type === 'sortante' 
                          ? 'bg-success/20 text-success' 
                          : 'bg-info/20 text-info'
                      }`}>
                        {invoice.invoice_type || 'entrante'}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Aucune facture
                </div>
              )}
            </div>
          </div>

          {/* Transactions bancaires */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <CreditCard className="text-secondary" size={20} />
              <h2 className="text-lg font-semibold text-foreground">
                Transactions récentes
              </h2>
            </div>
            
            <div className="space-y-3">
              {transactions.length > 0 ? (
                transactions.map((transaction) => (
                  <div 
                    key={transaction.id}
                    className="flex items-center justify-between p-3 bg-muted rounded-lg hover:bg-muted/70 transition-colors cursor-pointer"
                  >
                    <div>
                      <p className="font-medium text-foreground">{transaction.vendor || 'N/A'}</p>
                      <p className="text-sm text-muted-foreground">
                        {transaction.category || 'Non catégorisé'} • {new Date(transaction.date).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    <p className={`font-semibold ${
                      transaction.amount > 0 ? 'text-success' : 'text-destructive'
                    }`}>
                      {transaction.amount > 0 ? '+' : ''}{transaction.amount.toFixed(2)} €
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Aucune transaction
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Info */}
        {(!invoices.length && !transactions.length) && (
          <div className="card bg-blue-500/10 border-blue-500">
            <div className="flex gap-3">
              <AlertCircle className="text-blue-400 flex-shrink-0" size={24} />
              <div>
                <h3 className="font-semibold text-foreground mb-1">
                  Commencez par importer vos données
                </h3>
                <p className="text-sm text-muted-foreground">
                  Scannez vos emails Gmail pour extraire les factures, puis importez vos transactions bancaires pour voir vos statistiques.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

export default Dashboard

