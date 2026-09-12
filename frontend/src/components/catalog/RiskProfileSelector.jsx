export default function RiskProfileSelector({ currentProfile, options = [], actions = [], onAction }) {
  const select = (option) => {
    const action = actions[0];
    if (action && onAction) onAction({ ...action, args: { ...action.args, risk_profile: option.id } });
  };
  return (
    <div className="card">
      <div className="card-title">Tu perfil de inversión</div>
      <div className="card-subtitle">Elige el nivel de variación con el que te sientes cómodo.</div>
      <div className="profile-options">
        {options.map((option) => (
          <button key={option.id} className={`profile-option ${currentProfile === option.id ? "selected" : ""}`} onClick={() => select(option)}>
            <strong>{option.title}</strong><small>{option.description}</small>
          </button>
        ))}
      </div>
    </div>
  );
}
