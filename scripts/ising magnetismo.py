import numpy as np
import matplotlib.pyplot as plt
import random


def energy(state,B = 0, J = 1):
    N = len(state)
    interaction = 0
    for i in range(N):

        interaction += state[i] * state[(i + 1) % N] 

    E = -J * interaction - B * sum(state) # Asumiendo mu_b = 1
    return E

def trial_state(state):
    N = len(state)
    particles = [x for x in range(0,N)]
    particle = random.choice(particles)
    trial_state = state.copy()
    trial_state[particle] = - trial_state[particle]
    return trial_state


def isingmodel(N,T, B = 0, J = 1, n = 1000):

    ## Chose number of iterations required to reach equilibrium 
    if n < 10 * N:
        n = 10 * N
    else: 
        n = n
    

    ### This is a matrix that contains at each row the state of the system at each iteration
    states = np.zeros((n,N))

    spins = [1/2, -1/2]
    initial_state = list(map(lambda x: random.choice(spins), range(N))) ## Hot start
    

    ## Calculation of initial energy
    E = energy(initial_state,J,B)

    ### Generation of a trial configuration

    for i in range(n):
        if i == 0:
            states[i] = initial_state
        else: 
            current_state = states[i-1]
            E_current = energy(current_state,B,J)
        ## Generation of a trial configuration
            t_state = trial_state(current_state)
            E_trial = energy(t_state,J,B)
            if E_trial <= E_current:
                states[i] = t_state
            elif E_trial > E_current:
                DeltaE = E_trial - E_current
                R = np.exp(- DeltaE / (1 * T))
                r = random.uniform(0,1)
                if R >= r: 
                    states[i] = t_state
                else: 
                    states[i] = current_state
    
    return states


# ======= Params of simulation ====== 

N = 20 # Size of the chain 
T = 1 # Temperature in Kelvin - A low value to see domain formation
steps = 1000 # Number of iterations
B = 1 ## External magnetic field

# ==========================================
# Execute

historia_spins = isingmodel(N,T,B ,J=1,n=steps)
# --- View ---

plt.figure(figsize=(10, 6))
plt.imshow(historia_spins, aspect='auto', cmap='Greys', interpolation='none')
plt.title(f'Evolución de Dominios Magnéticos (Ising 1-D)\nTemperatura = {T}, N = {N}')
plt.xlabel('Posición del Espín en la Cadena')
plt.ylabel('Tiempo (Iteraciones)')
plt.colorbar(label='Espín (+1/2 , -1/2)')

# Muestra la figura
plt.show()

