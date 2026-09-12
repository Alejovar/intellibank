export default function InvestmentProductList({ products = [], actions = [], onAction }) {
  const select = (product) => {
    const action = actions[0];
    if (action && onAction) onAction({ ...action, args: { ...action.args, product_id: product.id, product_title: product.title } });
  };
  return (
    <div className="card">
      <div className="card-title">Opciones para ti</div>
      <div className="product-list">
        {products.map((product) => (
          <button className="product-row" key={product.id} onClick={() => select(product)}>
            <span className="product-icon" />
            <span><strong>{product.title}</strong><small>{product.description || `Riesgo ${product.risk} · ${product.rate}% anual`}</small></span>
            <i>›</i>
          </button>
        ))}
        {!products.length && <div className="saved-empty">No hay productos disponibles con esos criterios.</div>}
      </div>
    </div>
  );
}
