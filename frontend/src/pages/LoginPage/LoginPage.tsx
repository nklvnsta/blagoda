import { useState, type SubmitEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import logoSrc from '/logo.png';
import { useAuth } from '../../auth/AuthContext';
import { defaultRouteForRole } from '../../navigation/access';
import {
  BoxStackIcon,
  ChartTrendIcon,
  EyeIcon,
  EyeOffIcon,
  HelpCircleIcon,
  LockIcon,
  TruckIcon,
  UserIcon,
} from '../../components/icons';
import styles from './LoginPage.module.css';

const FEATURES = [
  { icon: ChartTrendIcon, label: 'Прогноз спроса' },
  { icon: BoxStackIcon, label: 'Контроль остатков' },
  { icon: TruckIcon, label: 'Поставки и отгрузки' },
] as const;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;

    setError(null);
    setSubmitting(true);

    try {
      const user = await login(username.trim(), password);
      navigate(defaultRouteForRole(user.role), { replace: true });
    } catch {
      setError('Неверный логин или пароль');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.page}>
      <section className={styles.infoPanel} aria-label="О системе">
        <img src={logoSrc} alt="Благода" className={styles.logo} />

        <h1 className={styles.infoTitle}>Оптимизация товарных потоков</h1>
        <p className={styles.infoDescription}>
          Система предназначена для прогнозирования спроса, контроля остатков и формирования
          поставок для розничной сети «Благода»
        </p>

        <div className={styles.features}>
          {FEATURES.map(({ icon: Icon, label }) => (
            <div key={label} className={styles.feature}>
              <div className={styles.featureIcon}>
                <Icon size={60} />
              </div>
              <span className={styles.featureLabel}>{label}</span>
            </div>
          ))}
        </div>

        <div className={styles.infoNote}>
          <LockIcon size={38} className={styles.noteIcon} />
          <p className={styles.noteText}>
            Учётные данные выдаются администратором системы.
            <br />
            Самостоятельная регистрация пользователей не предусмотрена
          </p>
        </div>
      </section>

      <section className={styles.formPanel} aria-label="Вход в систему">
        <div className={styles.formCard}>
          <h2 className={styles.formTitle}>Вход в систему</h2>
          <p className={styles.formSubtitle}>Войдите в свой аккаунт для продолжения работы</p>

          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="login-username">
                Логин
              </label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIcon}>
                  <UserIcon size={25} />
                </span>
                <input
                  id="login-username"
                  className={styles.input}
                  type="text"
                  autoComplete="username"
                  placeholder="Введите логин"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="login-password">
                Пароль
              </label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIcon}>
                  <LockIcon size={25} />
                </span>
                <input
                  id="login-password"
                  className={styles.input}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Введите пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className={styles.togglePassword}
                  aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                  onClick={() => setShowPassword((v) => !v)}
                >
                  {showPassword ? <EyeOffIcon size={22} /> : <EyeIcon size={22} />}
                </button>
              </div>
            </div>

            {error && <p className={styles.error}>{error}</p>}

            <button type="submit" className={styles.submit} disabled={submitting}>
              {submitting ? 'Вход…' : 'Войти'}
            </button>
          </form>

          <p className={styles.help}>
            <HelpCircleIcon size={20} className={styles.helpIcon} />
            Забыли пароль? Обратитесь к администратору
          </p>
        </div>
      </section>
    </div>
  );
}
