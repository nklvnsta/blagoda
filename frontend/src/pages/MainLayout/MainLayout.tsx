import styles from './MainLayout.module.css'
import { Header } from '../../components/ui/Header'
import { Footer } from '../../components/ui/Footer'
import { Outlet } from 'react-router-dom'

export const MainLayout = () => {
  return (
    <div className={styles.mainLayout}>
      <Header />
      <main className={styles.content}>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};
