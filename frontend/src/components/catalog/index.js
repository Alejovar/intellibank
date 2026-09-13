/**
 * Registro del catalogo cerrado de componentes. Este mapa es la unica
 * fuente de verdad de que puede renderizar el frontend: si el backend
 * manda un "component" que no esta aqui, el A2UIRenderer lo trata como
 * error de catalogo (nunca intenta interpretarlo de otra forma).
 */
import BalanceCard from "./BalanceCard";
import MovementsTable from "./MovementsTable";
import ExpenseChart from "./ExpenseChart";
import BarChart from "./BarChart";
import OptionsList from "./OptionsList";
import PaymentSlider from "./PaymentSlider";
import TransferForm from "./TransferForm";
import SharedExpenseList from "./SharedExpenseList";
import ConfirmationSummary from "./ConfirmationSummary";
import SuccessScreen from "./SuccessScreen";
import InfoBanner from "./InfoBanner";
import TextBlock from "./TextBlock";
import MarketWatchlist from "./MarketWatchlist";
import CurrencyExchangeCard from "./CurrencyExchangeCard";
import PortfolioSummaryCard from "./PortfolioSummaryCard";
import InvestmentPositionCard from "./InvestmentPositionCard";
import PortfolioTable from "./PortfolioTable";
import PerformanceChart from "./PerformanceChart";
import CashflowTable from "./CashflowTable";
import InvestmentComparison from "./InvestmentComparison";
import InvestmentProductList from "./InvestmentProductList";
import RiskProfileSelector from "./RiskProfileSelector";
import BeforeAfterPortfolio from "./BeforeAfterPortfolio";
import SavingsGoalCard from "./SavingsGoalCard";

export const COMPONENT_REGISTRY = {
  BalanceCard, MovementsTable, ExpenseChart, BarChart, OptionsList, PaymentSlider,
  TransferForm, SharedExpenseList, ConfirmationSummary, SuccessScreen,
  InfoBanner, TextBlock, MarketWatchlist, CurrencyExchangeCard,
  PortfolioSummaryCard, InvestmentPositionCard, PortfolioTable,
  PerformanceChart, CashflowTable, InvestmentComparison,
  InvestmentProductList, RiskProfileSelector, BeforeAfterPortfolio, SavingsGoalCard,
};
