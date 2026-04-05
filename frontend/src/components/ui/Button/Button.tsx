import styles from "./Button.module.css";

interface ButtonProps {
    onClick: () => void;
    type?: "primary" | "secondary";
    linkButton?: boolean;
    icon?: React.ReactNode;
    children?: React.ReactNode;
}

export function Button({ onClick, type = "primary", linkButton, icon, children }: React.PropsWithChildren<ButtonProps>) {
    return (
        linkButton ? (
            <a className={`button ${type}`} href="#">
                {children}
                {icon && <span className={styles.icon}>{icon}</span>}
            </a>
        ) : (
            <button
                type="button"
                className={styles.button + (type === "secondary" ? ` ${styles.secondary}` : "")}
                onClick={onClick}
            >
                {children}
                {icon && <span className={styles.icon}>{icon}</span>}
            </button>
        )
    );
}