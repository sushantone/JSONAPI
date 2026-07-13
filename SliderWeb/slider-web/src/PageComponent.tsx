function PageComponent({
    page,
    index,
    pagesCount,
    translateX,
    holeMarginLeft,
    navHovered,
    isActivePage,
    onNavEnter,
    onNavLeave,
}: {
    page: any;
    index: number;
    pagesCount: number;
    translateX: number;
    holeMarginLeft: number;
    navHovered: boolean;
    isActivePage: boolean;
    onNavEnter: () => void;
    onNavLeave: () => void;
}) {
    return (
        <div
            key={page.id}
            className="page"
            style={{
                zIndex: `${1000 - (index * 100)}`,
                transform: `translateX(${translateX}%)`,
            }}
        >
            <div className="page-content" style={{ backgroundColor: page.background }}>
                <h1>{page.name}</h1>
                <p>{page.description}</p>
            </div>
            <div className="page-nav">
                <div className="page-nav-left" style={{ backgroundColor: page.background }}></div>
                <div
                    className="page-nav-right"
                    onMouseEnter={onNavEnter}
                    onMouseLeave={onNavLeave}
                >
                    <div className="page-nav-hole-wrap">
                        <div
                            className={`page-nav-hole${isActivePage ? ' active' : ''}`}
                            style={{
                                borderColor: page.background,
                                right: navHovered ? '0' : `${holeMarginLeft}vh`,
                                ['--hole-expanded-width' as string]: `${(pagesCount - index) * 15}vh`,
                                transitionDelay: `${index * 0.06}s`,
                            }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default PageComponent;
