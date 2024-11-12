import React, { useEffect, useState } from 'react';
import { IoMoon } from "react-icons/io5";
import { IoSunny } from "react-icons/io5";
import { IconContext } from "react-icons";

const DarkModeToggle: React.FC = () => {
    const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

    // Initialize theme from localStorage
    useEffect(() => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark') {
            setIsDarkMode(true);
            document.documentElement.classList.add('dark');
        } else {
            setIsDarkMode(false);
            document.documentElement.classList.remove('dark');
        }
    }, []);

    // Toggle theme and save preference to localStorage
    const toggleDarkMode = () => {
        if (isDarkMode) {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        } else {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        }
        setIsDarkMode(!isDarkMode);
    };

    return (
        <button
            aria-label="Toggle dark mode"
            className="mx-10"
            onClick={toggleDarkMode}
        >
            
                {isDarkMode ? <IconContext.Provider value={{ color: "white"}}><IoSunny/></IconContext.Provider> : <IconContext.Provider value={{ color: "black"}}><IoMoon/></IconContext.Provider>}
            
        </button>
    );
};

export default DarkModeToggle;
