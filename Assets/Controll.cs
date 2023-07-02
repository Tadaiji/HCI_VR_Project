using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Video;

public class Controll : MonoBehaviour
{
    [SerializeField]
    private Camera mainCamera;

    [SerializeField]
    private GameObject player;
    
    [SerializeField]
    private GameObject visibCollider;
    
    [SerializeField]
    private VideoPlayer videoPlayer;

    public double clockTimeVideo = 0;
    
    public bool paused = false;
    
    public int currentIndex = 0;
    
    public List<double> stopTimes;
    
    [SerializeField]
    private List<GameObject> targets;

    

    // Update is called once per frame
    void Update()
    {
        if (clockTimeVideo >= stopTimes[currentIndex])
        {
            if (!paused)
            {
                videoPlayer.Pause();
                paused = true;
                targets[currentIndex].SetActive(true);
                visibCollider.SetActive(true);
                VisualTrail();
            }
        }
        else
        {
            if (videoPlayer != null)
                clockTimeVideo = videoPlayer.clockTime;
        }
        
        /*
        if (paused)
        {
            
            
            
            //Cast Raycast until hit
            RaycastHit hit;
            Ray ray = mainCamera.ScreenPointToRay(Input.mousePosition);
        
            if(Physics.Raycast(mainCamera.transform.position, mainCamera.transform.forward, out hit)) {
                // Do something with the object that was hit by the raycast.
                print("raycast");
                Debug.DrawRay(hit.transform.position, Vector3.forward, Color.green);
                if(hit.collider.gameObject.tag == "target")
                    hit.collider.gameObject.SetActive(false);
                
            } 
            //When target hit then startVideoAgain()
        }
        */
    }


    public void StartVideoAgain()
    {
        videoPlayer.Play();
        paused = false;
    }

    public void Collision(Collider collision)
    {
        print("collision");
        if (collision.gameObject == targets[currentIndex])
        {
            StartVideoAgain();
            targets[currentIndex].SetActive(false);
            visibCollider.SetActive(false);
            currentIndex += 1;
            Destroy(gameObject.GetComponent<LineRenderer>());
        }
    }

    public void VisualTrail()
    {
        //instanciate linerenderer
        LineRenderer line = gameObject.AddComponent<LineRenderer>();
        Gradient gradient = new Gradient();
        line.material = new Material(Shader.Find("Sprites/Default"));
        float alpha = 1.0f;
        float alpha2 = 0.2f;
        Color c1 = Color.blue;
        Color c2 = Color.white;
        
        gradient.SetKeys(
            new GradientColorKey[] { new GradientColorKey(c1, 0.0f), new GradientColorKey(c2, 1.0f) },
            new GradientAlphaKey[] { new GradientAlphaKey(alpha, 0.0f), new GradientAlphaKey(alpha2, 1.0f) }
        );
        line.colorGradient = gradient;
        line.SetPosition(0, visibCollider.transform.position);
        line.SetPosition(1, targets[currentIndex].transform.position);
        //give line renderer current position of visibCollider and targets[currentIndex]
    }

}
