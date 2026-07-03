function PageComponent({ page, index, pages }: { page: any, index: number, pages: any[] }) {
    return (
        <div key={page.id} className="page" style={{ zIndex: `${1000 - (index * 100)}` }}>
            <div className="page-content"
                style={{ backgroundColor: page.background }}>
                <h1>{page.name}</h1>
                <p>{page.description}</p>
            </div>
            <div className="page-nav">
                <div className="page-nav-left" style={{ backgroundColor: page.background }}></div>
                <div className="page-nav-right">
                    <div className="page-nav-hole-wrap">
                        <div className="page-nav-hole" style={{ borderColor: page.background, marginLeft: `${index*1}vh` }}></div>
                    </div>
                    <nav className="page-nav-popup">
                        {pages.map((item) => (
                            <a
                                key={item.id}
                                href={`#page-${item.id}`}
                                className={item.id === page.id ? 'page-nav-popup-item active' : 'page-nav-popup-item'}
                                style={{ borderLeftColor: item.background }}
                            >
                                {item.name}
                            </a>
                        ))}
                    </nav>
                </div>
            </div>
        </div>
    );
}

export default PageComponent;