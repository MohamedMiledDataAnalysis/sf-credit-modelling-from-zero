"""sfrating: the teaching rating model built in *Structured Finance Credit Modelling from Zero*.

Modules, in the order the book builds them:
    data          Chapter 4   load the datasets
    numerics      Chapter 7   bisection, Newton, trapezoid, Simpson
    merton        Chapter 9   structural model of default
    pd_model      Chapters 6, 10  logistic PD model and expected loss
    rollrate      Chapter 11  Markov roll-rate model
    survival      Chapter 12  Kaplan-Meier time to default
    vasicek       Chapter 13  one-factor model and copula simulation
    loss_dist     Chapter 14  pool loss distribution
    rmbs          Chapter 15  rating-level default frequency and severity
    cmbs          Chapter 16  DSCR, LTV and refinancing test
    abs_auto      Chapter 17  static-pool loss curves
    clo           Chapter 18  diversity score and binomial expansion
    cashflow      Chapter 19  pool cashflows and waterfall
    rating        Chapter 20  scenarios and rating assignment
    report        Chapter 21  LaTeX model report
"""
__version__ = "1.0.0"
