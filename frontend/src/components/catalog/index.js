/**
 * Registro del catalogo cerrado de componentes. Este mapa es la unica
 * fuente de verdad de que puede renderizar el frontend: si el backend
 * manda un "component" que no esta aqui, el A2UIRenderer lo trata como
 * error de catalogo (nunca intenta interpretarlo de otra forma).
 */
import BalanceCard from "./BalanceCard";
import MovementsTable from "./MovementsTable";
import ExpenseChart from "./ExpenseChart";
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

export const COMPONENT_REGISTRY = {
  BalanceCard, MovementsTable, ExpenseChart, OptionsList, PaymentSlider,
  TransferForm, SharedExpenseList, ConfirmationSummary, SuccessScreen,
  InfoBanner, TextBlock, MarketWatchlist, CurrencyExchangeCard,
};
