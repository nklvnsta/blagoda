import styles from './MainLayout.module.css'
import { Header } from '../../components/ui/Header'
import { Footer } from '../../components/ui/Footer'
import { SectionNavigation } from '../../components/ui/SectionNavigation'
import { Outlet } from 'react-router-dom'

export const MainLayout = () => {
  return (
    <div className={styles.mainLayout}>
      <Header />
      <SectionNavigation className={styles.navigation} />
      <main className={styles.content}>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};
